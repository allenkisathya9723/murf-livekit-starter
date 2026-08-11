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
