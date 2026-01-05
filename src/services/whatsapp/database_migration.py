"""Database migration for WhatsApp conversation tables."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger(__name__)


class WhatsAppDatabaseMigration:
    """Handle WhatsApp-related database migrations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database migration.

        Args:
            db_path: Path to database (default: data/clinic.db)
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def run_migrations(self):
        """Run all WhatsApp database migrations."""
        logger.info("Running WhatsApp database migrations...")

        try:
            self._create_conversations_table()
            self._create_messages_table()
            self._create_escalations_table()
            logger.info("WhatsApp database migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running WhatsApp migrations: {e}")
            return False

    def _create_conversations_table(self):
        """Create whatsapp_conversations table."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='whatsapp_conversations'
            """)

            if cursor.fetchone():
                logger.info("whatsapp_conversations table already exists")
                return

            # Create table
            cursor.execute("""
                CREATE TABLE whatsapp_conversations (
                    id TEXT PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    last_message_time TIMESTAMP,
                    last_message_content TEXT,
                    unread_count INTEGER DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_patient
                ON whatsapp_conversations(patient_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_last_message
                ON whatsapp_conversations(last_message_time DESC)
            """)

            conn.commit()
            logger.info("Created whatsapp_conversations table")

        except Exception as e:
            logger.error(f"Error creating whatsapp_conversations table: {e}")
            raise
        finally:
            conn.close()

    def _create_messages_table(self):
        """Create whatsapp_messages table."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='whatsapp_messages'
            """)

            if cursor.fetchone():
                logger.info("whatsapp_messages table already exists")
                return

            # Create table
            cursor.execute("""
                CREATE TABLE whatsapp_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    conversation_id TEXT NOT NULL,
                    patient_id INTEGER NOT NULL,
                    content TEXT,
                    message_type TEXT DEFAULT 'text',
                    is_outgoing BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'sent',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reply_to_id TEXT,
                    attachment_url TEXT,
                    attachment_type TEXT,
                    is_starred BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id),
                    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_conversation
                ON whatsapp_messages(conversation_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_patient
                ON whatsapp_messages(patient_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_message_id
                ON whatsapp_messages(message_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_status
                ON whatsapp_messages(status)
            """)

            conn.commit()
            logger.info("Created whatsapp_messages table")

        except Exception as e:
            logger.error(f"Error creating whatsapp_messages table: {e}")
            raise
        finally:
            conn.close()

    def _create_escalations_table(self):
        """Create whatsapp_escalations table."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='whatsapp_escalations'
            """)

            if cursor.fetchone():
                logger.info("whatsapp_escalations table already exists")
                return

            # Create table
            cursor.execute("""
                CREATE TABLE whatsapp_escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    patient_id INTEGER NOT NULL,
                    urgency TEXT DEFAULT 'medium',
                    reason TEXT,
                    detected_symptoms TEXT,
                    status TEXT DEFAULT 'pending',
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    resolution_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_escalations_patient
                ON whatsapp_escalations(patient_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_escalations_status
                ON whatsapp_escalations(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_whatsapp_escalations_urgency
                ON whatsapp_escalations(urgency, created_at DESC)
            """)

            conn.commit()
            logger.info("Created whatsapp_escalations table")

        except Exception as e:
            logger.error(f"Error creating whatsapp_escalations table: {e}")
            raise
        finally:
            conn.close()

    def rollback_migrations(self):
        """Rollback WhatsApp database migrations (drop tables)."""
        logger.warning("Rolling back WhatsApp database migrations...")

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Drop tables in reverse order (to respect foreign keys)
            cursor.execute("DROP TABLE IF EXISTS whatsapp_escalations")
            cursor.execute("DROP TABLE IF EXISTS whatsapp_messages")
            cursor.execute("DROP TABLE IF EXISTS whatsapp_conversations")

            conn.commit()
            logger.info("WhatsApp database migrations rolled back")

        except Exception as e:
            logger.error(f"Error rolling back WhatsApp migrations: {e}")
            raise
        finally:
            conn.close()


def run_whatsapp_migrations(db_path: Optional[str] = None) -> bool:
    """Run WhatsApp database migrations.

    Args:
        db_path: Path to database (default: data/clinic.db)

    Returns:
        True if successful, False otherwise
    """
    migration = WhatsAppDatabaseMigration(db_path=db_path)
    return migration.run_migrations()


if __name__ == "__main__":
    # Run migrations when script is executed directly
    logging.basicConfig(level=logging.INFO)
    success = run_whatsapp_migrations()
    if success:
        print("WhatsApp database migrations completed successfully!")
    else:
        print("WhatsApp database migrations failed!")
