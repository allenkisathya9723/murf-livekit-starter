import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agent import Assistant
from database import delete_user, get_user, init_db, save_user


def _patch_db(test_db):
    """Return a context manager that redirects agent DB calls to the test database."""
    return (
        patch("agent.get_user", lambda uid: get_user(uid, db_path=test_db)),
        patch(
            "agent.save_user",
            lambda **kwargs: __import__("database").save_user(
                **kwargs, db_path=test_db
            ),
        ),
        patch("agent.delete_user", lambda uid: delete_user(uid, db_path=test_db)),
    )


@pytest.mark.asyncio
async def test_lookup_existing_caller():
    """Memory tool test 1: lookup existing caller returns found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)
        save_user(
            user_id="existing_user",
            name="Sathya",
            language_preference="Telugu",
            facts={"preferred_facility": "PHC"},
            db_path=test_db,
        )

        assistant = Assistant(user_id="existing_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            res = await assistant.lookup_caller(context=None)
            data = json.loads(res)
            assert data["status"] == "found"
            assert data["name"] == "Sathya"
            assert data["language_preference"] == "Telugu"
            assert data["facts"]["preferred_facility"] == "PHC"


@pytest.mark.asyncio
async def test_lookup_missing_caller():
    """Memory tool test 2: lookup missing caller returns not_found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        assistant = Assistant(user_id="unknown_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            res = await assistant.lookup_caller(context=None)
            data = json.loads(res)
            assert data["status"] == "not_found"


@pytest.mark.asyncio
async def test_save_without_consent_refused():
    """Memory tool test 3: save without consent → REFUSED, no DB write."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        assistant = Assistant(user_id="no_consent_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            res = await assistant.save_caller_info(
                context=None,
                name="Sathya",
                language_preference="Telugu",
                facts='{"preferred_facility": "PHC"}',
                user_consented=False,
            )
            assert "ERROR" in res

        # Verify no database write occurred
        assert get_user("no_consent_user", db_path=test_db) is None


@pytest.mark.asyncio
async def test_save_with_default_consent_refused():
    """Verify that omitting user_consented defaults to False and is refused."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        assistant = Assistant(user_id="default_consent_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            # Call without user_consented — should default to False
            res = await assistant.save_caller_info(
                context=None,
                name="Sathya",
                language_preference="Telugu",
                facts="{}",
            )
            assert "ERROR" in res

        assert get_user("default_consent_user", db_path=test_db) is None


@pytest.mark.asyncio
async def test_save_with_consent_succeeds():
    """Memory tool test 4: save with consent → SUCCESS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        assistant = Assistant(user_id="consent_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            res = await assistant.save_caller_info(
                context=None,
                name="Sathya",
                language_preference="Telugu",
                facts='{"preferred_facility": "PHC"}',
                user_consented=True,
            )
            assert "Successfully saved" in res

        user = get_user("consent_user", db_path=test_db)
        assert user is not None
        assert user["name"] == "Sathya"


@pytest.mark.asyncio
async def test_forget_caller_deletes():
    """Memory tool test 5: forget caller → DELETED."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        # Pre-populate
        save_user(
            user_id="forget_user",
            name="Sathya",
            language_preference="Telugu",
            db_path=test_db,
        )

        assistant = Assistant(user_id="forget_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            res = await assistant.forget_caller(context=None)
            assert "Successfully deleted" in res

            # Re-lookup should return not_found
            lookup = await assistant.lookup_caller(context=None)
            data = json.loads(lookup)
            assert data["status"] == "not_found"


@pytest.mark.asyncio
async def test_full_consent_lifecycle():
    """End-to-end: new caller → no-consent save fails → consent save succeeds →
    returning caller recognized → forget → treated as new."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "test.db"
        init_db(test_db)

        # 1. New caller
        assistant1 = Assistant(user_id="lifecycle_user")
        p1, p2, p3 = _patch_db(test_db)
        with p1, p2, p3:
            lookup1 = await assistant1.lookup_caller(context=None)
            assert json.loads(lookup1)["status"] == "not_found"

            # 2. Save without consent — refused
            no_consent = await assistant1.save_caller_info(
                context=None,
                name="Sathya",
                language_preference="Telugu",
                facts='{"preferred_facility": "PHC"}',
                user_consented=False,
            )
            assert "ERROR" in no_consent
            assert get_user("lifecycle_user", db_path=test_db) is None

            # 3. Save with consent — succeeds
            consent = await assistant1.save_caller_info(
                context=None,
                name="Sathya",
                language_preference="Telugu",
                facts='{"preferred_facility": "PHC"}',
                user_consented=True,
            )
            assert "Successfully saved" in consent

        # 4. Returning caller (simulate backend restart)
        assistant2 = Assistant(user_id="lifecycle_user")
        with p1, p2, p3:
            lookup2 = await assistant2.lookup_caller(context=None)
            data2 = json.loads(lookup2)
            assert data2["status"] == "found"
            assert data2["name"] == "Sathya"
            assert data2["language_preference"] == "Telugu"
            assert data2["facts"]["preferred_facility"] == "PHC"

            # 5. Forget me
            forget = await assistant2.forget_caller(context=None)
            assert "Successfully deleted" in forget

            # 6. Now treated as new
            lookup3 = await assistant2.lookup_caller(context=None)
            assert json.loads(lookup3)["status"] == "not_found"
