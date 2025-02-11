import sqlite3
from datetime import datetime


class ConversationDB:
    def __init__(self, db_path="data/conversations.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Creates the conversations table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
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
        self.conn.commit()

    def create_conversation(self):
        """Creates a new conversation and returns its session ID."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        created_at = datetime.now().isoformat()
        self.cursor.execute(
            """
            INSERT INTO conversations (session_id, created_at, updated_at)
            VALUES (?, ?, ?)
        """,
            (session_id, created_at, created_at),
        )
        self.conn.commit()
        return session_id

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

    def get_conversations(self):
        """Retrieves all conversations."""
        self.cursor.execute(
            "SELECT session_id, created_at FROM conversations ORDER BY created_at DESC"
        )
        return self.cursor.fetchall()

    def get_messages(self, session_id):
        """Retrieves all messages for a specific conversation."""
        self.cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return self.cursor.fetchall()

    def delete_conversation(self, session_id):
        """Deletes a conversation and its messages."""
        self.cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.cursor.execute(
            "DELETE FROM conversations WHERE session_id = ?", (session_id,)
        )
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()
