import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("janmitra.database")

# Default database location: backend/data/janmitra.db
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "janmitra.db"


def _get_db_path(custom_path: Optional[Path | str] = None) -> Path:
    path = Path(custom_path) if custom_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection(db_path: Optional[Path | str] = None):
    path = _get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Optional[Path | str] = None) -> None:
    path = _get_db_path(db_path)
    logger.info(f"Initializing database at: {path}")

    with get_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT NOT NULL DEFAULT '{}',
                last_interaction TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                reference_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                caller_id TEXT,
                reason TEXT NOT NULL,
                summary TEXT NOT NULL,
                what_checked TEXT NOT NULL,
                urgency TEXT NOT NULL,
                language TEXT NOT NULL,
                preferred_follow_up TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN'
            );
            """
        )
        conn.commit()


def get_user(
    user_id: str, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    if not user_id:
        return None

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, name, language_preference, facts, last_interaction, created_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            user_data = dict(row)
            try:
                user_data["facts"] = (
                    json.loads(user_data["facts"]) if user_data["facts"] else {}
                )
            except Exception as e:
                logger.warning(f"Failed to parse facts JSON for user {user_id}: {e}")
                user_data["facts"] = {}

            return user_data
    except Exception as e:
        logger.error(f"Database error in get_user({user_id}): {e}")
        return None


def save_user(
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = None,
    facts: Optional[dict[str, Any] | str] = None,
    db_path: Optional[Path | str] = None,
) -> Optional[dict[str, Any]]:
    if not user_id:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()

    # Parse facts dict
    new_facts: dict[str, Any] = {}
    if isinstance(facts, str):
        try:
            new_facts = json.loads(facts)
        except Exception:
            new_facts = {"note": facts}
    elif isinstance(facts, dict):
        new_facts = facts

    try:
        existing = get_user(user_id, db_path=db_path)
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            if existing:
                updated_name = name if name is not None else existing.get("name")
                updated_lang = (
                    language_preference
                    if language_preference is not None
                    else existing.get("language_preference")
                )
                merged_facts = existing.get("facts", {})
                if isinstance(merged_facts, dict):
                    merged_facts.update(new_facts)
                else:
                    merged_facts = new_facts

                facts_json = json.dumps(merged_facts)
                cursor.execute(
                    """
                    UPDATE users
                    SET name = ?, language_preference = ?, facts = ?, last_interaction = ?
                    WHERE user_id = ?
                    """,
                    (updated_name, updated_lang, facts_json, now_iso, user_id),
                )
            else:
                facts_json = json.dumps(new_facts)
                cursor.execute(
                    """
                    INSERT INTO users (user_id, name, language_preference, facts, last_interaction, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        name or "",
                        language_preference or "",
                        facts_json,
                        now_iso,
                        now_iso,
                    ),
                )
            conn.commit()

        return get_user(user_id, db_path=db_path)
    except Exception as e:
        logger.error(f"Database error in save_user({user_id}): {e}")
        return None


def delete_user(user_id: str, db_path: Optional[Path | str] = None) -> bool:
    if not user_id:
        return False

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Database error in delete_user({user_id}): {e}")
        return False


def get_escalation(
    reference_id: str, db_path: Optional[Path | str] = None
) -> Optional[dict[str, Any]]:
    if not reference_id:
        return None

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT reference_id, created_at, caller_id, reason, summary,
                       what_checked, urgency, language, preferred_follow_up, status
                FROM escalations WHERE reference_id = ?
                """,
                (reference_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Database error in get_escalation({reference_id}): {e}")
        return None


def save_escalation(
    reason: str,
    summary: str,
    what_checked: str,
    urgency: str = "Medium",
    language: str = "English",
    preferred_follow_up: str = "Phone",
    caller_id: Optional[str] = "default_user",
    db_path: Optional[Path | str] = None,
) -> Optional[dict[str, Any]]:
    import random
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    rand_num = random.randint(100, 999)
    ref_id = f"JM-{date_str}-{rand_num}"
    created_at = now.isoformat()

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO escalations (
                    reference_id, created_at, caller_id, reason, summary,
                    what_checked, urgency, language, preferred_follow_up, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ref_id,
                    created_at,
                    caller_id or "unknown_caller",
                    reason,
                    summary,
                    what_checked,
                    urgency,
                    language,
                    preferred_follow_up,
                    "OPEN",
                ),
            )
            conn.commit()
        return get_escalation(ref_id, db_path=db_path)
    except Exception as e:
        logger.error(f"Database error in save_escalation: {e}")
        return None


def get_escalations(db_path: Optional[Path | str] = None) -> list[dict[str, Any]]:
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT reference_id, created_at, caller_id, reason, summary,
                       what_checked, urgency, language, preferred_follow_up, status
                FROM escalations ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Database error in get_escalations: {e}")
        return []

