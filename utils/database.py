import sqlite3
from datetime import datetime
import os
import logging
import threading
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class ConversationDB:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path="data/conversations.db"):
        """Initialize the database connection, create necessary directories, and set up the database."""

        # Ensure the directory for the database exists
        db_directory = Path(db_path).parent
        if not db_directory.exists():
            try:
                db_directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {db_directory}")
            except OSError as e:
                logger.error(f"Error creating database directory: {e}")
                raise

        # Check if already initialized to avoid re-initialization
        if not hasattr(self, "initialized"):
            try:
                # Establish the SQLite database connection
                self.conn = sqlite3.connect(db_path, check_same_thread=False)
                # Enable WAL (Write-Ahead Logging) for better concurrency and performance
                self.conn.execute("PRAGMA journal_mode=WAL")
                # Set the synchronization mode to normal for better performance
                self.conn.execute("PRAGMA synchronous=NORMAL")
                # Set a 2MB cache size for improved performance
                self.conn.execute("PRAGMA cache_size=-2000")

                # Lock for thread-safety
                self._lock = threading.Lock()

                # Create the necessary tables
                self._create_table()

                # Mark the initialization flag
                self.initialized = True
            except sqlite3.Error as e:
                logger.error(f"Error initializing the database: {e}")
                raise

        # Initialize local storage
        from components.local_storage import LocalStorageManager

        self.local_storage = LocalStorageManager()

        # Sync with local storage if available
        self._sync_with_local_storage()

    def _sync_with_local_storage(self):
        """Sync database with local storage per session."""
        try:
            cursor = self.conn.cursor()
            # Get all sessions
            cursor.execute("SELECT session_id FROM conversations")
            sessions = cursor.fetchall()

            for (session_id,) in sessions:
                # Load session-specific data
                notes_key = f"notes_{session_id}"
                chats_key = f"chats_{session_id}"

                stored_notes = self.local_storage.load_data(notes_key)
                stored_chats = self.local_storage.load_data(chats_key)

                if stored_notes:
                    # Merge notes
                    self._merge_stored_notes(session_id, stored_notes)

                if stored_chats:
                    # Merge chats
                    self._merge_stored_chats(session_id, stored_chats)

            cursor.close()
        except Exception as e:
            logger.error(f"Error syncing with local storage: {e}")

    def _create_table(self):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    name TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(session_id) REFERENCES conversations(session_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    file_path TEXT UNIQUE,
                    file_name TEXT,
                    uploaded_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES conversations(session_id),
                    UNIQUE(session_id, file_name)
                )
            """)
            self.conn.commit()
            # Create indexes for faster lookup on session_id
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_session_id ON files(session_id);"
            )
            self.conn.commit()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    file_path TEXT UNIQUE,
                    file_type TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    conversation_id TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(session_id)
                )
            """)
            self.conn.commit()

            # Add index for file paths to speed up deletion queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_path 
                ON files(file_path);
            """)
            self.conn.commit()

            cursor.close()

    def create_conversation(self):
        """Creates a new conversation and returns its session ID."""
        with self._lock:
            cursor = self.conn.cursor()
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            created_at = datetime.now().isoformat()
            default_name = "New Conversation"
            cursor.execute(
                """
                INSERT INTO conversations (session_id, name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, default_name, created_at, created_at),
            )
            self.conn.commit()
            cursor.close()
            return session_id

    def update_conversation_name(self, session_id: str, name: str):
        """Updates the name of a conversation."""
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE conversations 
                    SET name = ?, updated_at = ?
                    WHERE session_id = ?
                    """,
                    (name, datetime.now().isoformat(), session_id),
                )
                self.conn.commit()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error updating conversation name: {e}")
            return False

    def get_conversation_name(self, session_id: str) -> str:
        """Retrieves the name of a conversation."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name FROM conversations WHERE session_id = ?", (session_id,)
            )
            result = cursor.fetchone()
            cursor.close()
        return result[0] if result else "Unnamed Conversation"

    def suggest_conversation_name(self, session_id: str) -> str:
        """Suggests a name based on the first user message."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT content 
                FROM messages 
                WHERE session_id = ? AND role = 'user' 
                ORDER BY timestamp ASC LIMIT 1
                """,
                (session_id,),
            )
            first_message = cursor.fetchone()
            cursor.close()
        if first_message:
            raw_title = first_message[0].strip()
            starters = [
                "what is",
                "how to",
                "can you",
                "please",
                "tell me about",
                "explain",
            ]
            for starter in starters:
                if raw_title.lower().startswith(starter):
                    raw_title = raw_title[len(starter) :].strip()
            title = " ".join(word.capitalize() for word in raw_title.split())
            if len(title) > 50:
                breakpoint = title[:50].rfind(" ")
                if breakpoint == -1:
                    breakpoint = 50
                title = title[:breakpoint].strip() + "..."
            return f"💬 {title}"
        return "New Conversation"

    def add_message(self, session_id, role, content):
        """Adds a message with proper session handling."""
        timestamp = datetime.now().isoformat()
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO messages (session_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, role, content, timestamp),
                )
                self.conn.commit()
                cursor.close()

                # Update local storage for this session
                chats_key = f"chats_{session_id}"
                stored_chats = self.local_storage.load_data(chats_key) or []
                stored_chats.append(
                    {"role": role, "content": content, "timestamp": timestamp}
                )
                self.local_storage.save_data(chats_key, stored_chats)

            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    def add_file(self, session_id, file_path, file_name):
        """Tracks a file associated with a conversation."""
        try:
            # Verify file path contains session ID
            if session_id not in file_path:
                logger.error(
                    f"File path {file_path} does not match session {session_id}"
                )
                return False
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE session_id = ? AND file_name = ?",
                    (session_id, file_name),
                )
                result = cursor.fetchone()
                count = result[0] if result and result[0] is not None else 0
                if count > 0:
                    logger.warning(
                        f"File {file_name} already exists in session {session_id}"
                    )
                    cursor.close()
                    return False
                timestamp = datetime.now().isoformat()
                cursor.execute(
                    """
                    INSERT INTO files (session_id, file_path, file_name, uploaded_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, file_path, file_name, timestamp),
                )
                self.conn.commit()
                cursor.close()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"File {file_name} already exists in session {session_id}")
            with self._lock:
                self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Error adding file to database: {e}")
            with self._lock:
                self.conn.rollback()
            return False

    def get_conversations(self):
        """Retrieves all conversations."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT session_id, created_at FROM conversations ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def get_conversation_details(self):
        """Retrieves all conversations with additional details."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    c.session_id,
                    c.created_at,
                    COUNT(DISTINCT m.id) as message_count,
                    COUNT(DISTINCT f.id) as file_count,
                    GROUP_CONCAT(DISTINCT f.file_name) as files
                FROM conversations c
                LEFT JOIN messages m ON c.session_id = m.session_id
                LEFT JOIN files f ON c.session_id = f.session_id
                GROUP BY c.session_id
                ORDER BY c.created_at DESC
            """)
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def get_messages(self, session_id):
        """Retrieves all messages for a specific conversation."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def get_conversation_files(self, session_id):
        """Gets all files associated with a conversation."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT file_path, file_name 
                FROM files 
                WHERE session_id = ?
                ORDER BY uploaded_at
                """,
                (session_id,),
            )
            files = cursor.fetchall()
            cursor.close()
        # Filter out non-existent files
        return [(fp, fn) for fp, fn in files if os.path.exists(fp)]

    def delete_conversation(self, session_id):
        """Deletes a conversation and cleans up local storage."""
        try:
            # Get files to delete
            files = self.get_conversation_files(session_id)
            # Delete files from disk
            for file_path, _ in files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM files WHERE session_id = ?", (session_id,))
                cursor.execute(
                    "DELETE FROM messages WHERE session_id = ?", (session_id,)
                )
                cursor.execute(
                    "DELETE FROM conversations WHERE session_id = ?", (session_id,)
                )
                self.conn.commit()
                cursor.close()

            # Clean up local storage
            self.local_storage.save_data(f"notes_{session_id}", [])
            self.local_storage.save_data(f"chats_{session_id}", [])
            self.local_storage.save_data(f"query_cache_{session_id}", {})

            return True
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False

    def delete_file(self, session_id: str, file_path: str):
        """Deletes a specific file from the database and disk."""
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "DELETE FROM files WHERE session_id = ? AND file_path = ?",
                    (session_id, file_path),
                )
                self.conn.commit()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            with self._lock:
                self.conn.rollback()
            return False

    def add_note(
        self,
        title: str,
        content: str,
        file_path: str,
        file_type: str,
        conversation_id: str = None,
    ):
        """Add a new note to the database and sync to local storage."""
        timestamp = datetime.now().isoformat()
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO notes (title, content, file_path, file_type, created_at, updated_at, conversation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        content,
                        file_path,
                        file_type,
                        timestamp,
                        timestamp,
                        conversation_id,
                    ),
                )
                self.conn.commit()
                cursor.close()

                # Sync to local storage
                notes = self.get_notes()
                self.local_storage.sync_notes(notes)

            return True
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False

    def get_notes(self):
        """Get all notes."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT title, content, file_path, file_type, created_at, conversation_id
                FROM notes
                ORDER BY created_at DESC
            """)
            notes = cursor.fetchall()
            cursor.close()
        return notes

    def delete_note(self, file_path: str) -> bool:
        """Delete a note from the database."""
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM notes WHERE file_path = ?", (file_path,))
                self.conn.commit()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting note from database: {e}")
            with self._lock:
                self.conn.rollback()
            return False

    def update_note_title(self, file_path: str, new_title: str):
        """Update a note's title."""
        try:
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE notes 
                    SET title = ?, updated_at = ?
                    WHERE file_path = ?
                    """,
                    (new_title, datetime.now().isoformat(), file_path),
                )
                self.conn.commit()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error updating note title: {e}")
            return False

    def close(self):
        """Closes the database connection."""
        with self._lock:
            self.conn.close()
