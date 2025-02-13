import sqlite3
from datetime import datetime
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ConversationDB:
    def __init__(self, db_path="data/conversations.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Creates the necessary tables if they don't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                name TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES conversations(session_id)
            )
        """)

        # Add files table with unique constraint
        self.cursor.execute("""
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

    def create_conversation(self):
        """Creates a new conversation and returns its session ID."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        created_at = datetime.now().isoformat()
        default_name = "New Conversation"
        self.cursor.execute(
            """
            INSERT INTO conversations (session_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, default_name, created_at, created_at),
        )
        self.conn.commit()
        return session_id

    def update_conversation_name(self, session_id: str, name: str):
        """Updates the name of a conversation."""
        try:
            self.cursor.execute(
                """
                UPDATE conversations 
                SET name = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (name, datetime.now().isoformat(), session_id),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating conversation name: {e}")
            return False

    def get_conversation_name(self, session_id: str) -> str:
        """Retrieves the name of a conversation."""
        self.cursor.execute(
            "SELECT name FROM conversations WHERE session_id = ?", (session_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else "Unnamed Conversation"

    def suggest_conversation_name(self, session_id: str) -> str:
        """Suggests a name based on the first user message."""
        self.cursor.execute(
            """
            SELECT content 
            FROM messages 
            WHERE session_id = ? AND role = 'user' 
            ORDER BY timestamp ASC LIMIT 1
            """,
            (session_id,),
        )
        first_message = self.cursor.fetchone()
        if first_message:
            # Truncate and clean the message to create a title
            name = first_message[0][:50].strip()
            if len(first_message[0]) > 50:
                name += "..."
            return name
        return "New Conversation"

    def add_message(self, session_id, role, content):
        """Adds a message to the specified conversation."""
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, role, content, timestamp),
        )
        self.conn.commit()

    def add_file(self, session_id, file_path, file_name):
        """Tracks a file associated with a conversation with session path verification."""
        try:
            # Verify file path contains session ID
            if session_id not in file_path:
                logger.error(
                    f"File path {file_path} does not match session {session_id}"
                )
                return False

            # Check if file already exists
            self.cursor.execute(
                "SELECT COUNT(*) FROM files WHERE session_id = ? AND file_name = ?",
                (session_id, file_name),
            )
            if self.cursor.fetchone()[0] > 0:
                logger.warning(
                    f"File {file_name} already exists in session {session_id}"
                )
                return False

            timestamp = datetime.now().isoformat()
            self.cursor.execute(
                """
                INSERT INTO files (session_id, file_path, file_name, uploaded_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, file_path, file_name, timestamp),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"File {file_name} already exists in session {session_id}")
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Error adding file to database: {e}")
            self.conn.rollback()
            return False

    def get_conversations(self):
        """Retrieves all conversations."""
        self.cursor.execute(
            "SELECT session_id, created_at FROM conversations ORDER BY created_at DESC"
        )
        return self.cursor.fetchall()

    def get_conversation_details(self):
        """Retrieves all conversations with additional details."""
        self.cursor.execute("""
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
        return self.cursor.fetchall()

    def get_messages(self, session_id):
        """Retrieves all messages for a specific conversation."""
        self.cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return self.cursor.fetchall()

    def get_conversation_files(self, session_id):
        """Gets all files associated with a conversation."""
        self.cursor.execute(
            """
            SELECT DISTINCT file_path, file_name 
            FROM files 
            WHERE session_id = ?
            ORDER BY uploaded_at
            """,
            (session_id,),
        )
        files = self.cursor.fetchall()
        # Filter out non-existent files
        return [(fp, fn) for fp, fn in files if os.path.exists(fp)]

    def delete_conversation(self, session_id):
        """Deletes a conversation, its messages, and associated files."""
        # Get files to delete
        files = self.get_conversation_files(session_id)

        # Delete files from disk
        for file_path, _ in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

        # Delete database records
        self.cursor.execute("DELETE FROM files WHERE session_id = ?", (session_id,))
        self.cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.cursor.execute(
            "DELETE FROM conversations WHERE session_id = ?", (session_id,)
        )
        self.conn.commit()

    def delete_file(self, session_id: str, file_path: str):
        """Deletes a specific file from the database and disk."""
        try:
            # Verify file belongs to session before deleting
            self.cursor.execute(
                """
                SELECT file_path 
                FROM files 
                WHERE session_id = ? AND file_path = ?
                """,
                (session_id, file_path),
            )
            if not self.cursor.fetchone():
                logger.warning(f"File {file_path} not found in session {session_id}")
                return False

            # Delete file from disk
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete from database
            self.cursor.execute(
                "DELETE FROM files WHERE session_id = ? AND file_path = ?",
                (session_id, file_path),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """Closes the database connection."""
        self.conn.close()
