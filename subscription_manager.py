import sqlite3
import secrets
import hashlib
import os
from datetime import datetime
from pathlib import Path

from utils.logger import setup_logger

DEFAULT_DB_PATH = str(Path(__file__).parent / "subscriptions.db")
logger = setup_logger("SubscriptionManager")


def get_db_path() -> str:
    """Get database path from config or use default."""
    try:
        from config import SERVER_CONFIG
        return SERVER_CONFIG.get("db_path") or DEFAULT_DB_PATH
    except (ImportError, KeyError):
        return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the subscriptions database."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            verified INTEGER DEFAULT 0,
            verification_token TEXT NOT NULL,
            subscribed_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscribers_email
        ON subscribers(email)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscribers_verified
        ON subscribers(verified)
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def add_subscriber(email: str) -> dict:
    """Add a new subscriber. Returns dict with status and verification_token."""
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO subscribers (email, verification_token) VALUES (?, ?)",
            (email, token)
        )
        conn.commit()
        logger.info(f"New subscriber added: {email}")
        return {"status": "success", "verification_token": token}
    except sqlite3.IntegrityError:
        # Email already exists - check if verified
        cursor = conn.execute(
            "SELECT verified, verification_token FROM subscribers WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            if row["verified"]:
                logger.info(f"Subscriber already verified: {email}")
                return {"status": "already_subscribed"}
            else:
                # Update token for re-send verification
                conn.execute(
                    "UPDATE subscribers SET verification_token = ?, updated_at = datetime('now') WHERE email = ?",
                    (token, email)
                )
                conn.commit()
                logger.info(f"Verification token refreshed for: {email}")
                return {"status": "pending", "verification_token": token}
        return {"status": "error", "message": "Unexpected database error"}
    except Exception as e:
        logger.error(f"Failed to add subscriber {email}: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


def verify_subscriber(email: str, token: str) -> bool:
    """Verify a subscriber's email address."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT verification_token FROM subscribers WHERE email = ? AND verified = 0",
            (email,)
        )
        row = cursor.fetchone()
        if row and row["verification_token"] == token:
            conn.execute(
                "UPDATE subscribers SET verified = 1, updated_at = datetime('now') WHERE email = ?",
                (email,)
            )
            conn.commit()
            logger.info(f"Subscriber verified: {email}")
            return True
        logger.warning(f"Invalid verification attempt for: {email}")
        return False
    except Exception as e:
        logger.error(f"Verification failed for {email}: {str(e)}")
        return False
    finally:
        conn.close()


def get_verified_subscribers() -> list:
    """Get all verified subscriber emails."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT email FROM subscribers WHERE verified = 1")
        return [row["email"] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to fetch subscribers: {str(e)}")
        return []
    finally:
        conn.close()


def remove_subscriber(email: str) -> bool:
    """Remove a subscriber by email."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM subscribers WHERE email = ?", (email,))
        conn.commit()
        logger.info(f"Subscriber removed: {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove subscriber {email}: {str(e)}")
        return False
    finally:
        conn.close()


def get_subscriber_count() -> int:
    """Get count of verified subscribers."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM subscribers WHERE verified = 1")
        return cursor.fetchone()["count"]
    except Exception as e:
        logger.error(f"Failed to count subscribers: {str(e)}")
        return 0
    finally:
        conn.close()


def get_total_count() -> int:
    """Get total count of all subscribers (verified + pending)."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM subscribers")
        return cursor.fetchone()["count"]
    except Exception as e:
        logger.error(f"Failed to count total subscribers: {str(e)}")
        return 0
    finally:
        conn.close()
