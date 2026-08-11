import tempfile
from pathlib import Path

from database import delete_user, get_user, init_db, save_user


class TestDatabaseInitialization:
    """Tests 1-2: initialization and directory creation."""

    def test_init_creates_db_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "sub" / "nested" / "test.db"
            init_db(test_db)
            assert test_db.exists()

    def test_init_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "deep" / "path" / "janmitra.db"
            init_db(test_db)
            assert test_db.parent.exists()
            assert test_db.exists()

    def test_double_init_does_not_destroy_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)
            save_user(
                user_id="persist_user",
                name="Sathya",
                language_preference="Telugu",
                db_path=test_db,
            )
            # Re-initialize — data must survive
            init_db(test_db)
            user = get_user("persist_user", db_path=test_db)
            assert user is not None
            assert user["name"] == "Sathya"


class TestInsertAndRetrieval:
    """Tests 3-4: insert and retrieval."""

    def test_save_and_retrieve_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            saved = save_user(
                user_id="user_123",
                name="Sathya",
                language_preference="Telugu",
                facts={"preferred_facility": "PHC", "age_band": "30s"},
                db_path=test_db,
            )
            assert saved is not None
            assert saved["name"] == "Sathya"
            assert saved["language_preference"] == "Telugu"
            assert saved["facts"]["preferred_facility"] == "PHC"
            assert saved["facts"]["age_band"] == "30s"

            retrieved = get_user("user_123", db_path=test_db)
            assert retrieved is not None
            assert retrieved["name"] == "Sathya"

    def test_missing_caller_returns_none(self):
        """Test 9: missing caller."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)
            assert get_user("nonexistent_user", db_path=test_db) is None

    def test_empty_user_id_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)
            assert get_user("", db_path=test_db) is None
            assert save_user(user_id="", db_path=test_db) is None
            assert delete_user("", db_path=test_db) is False


class TestJsonSerialization:
    """Test 5: JSON serialization/deserialization."""

    def test_dict_facts_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            facts = {"preferred_facility": "PHC", "topics": ["vaccination", "nutrition"]}
            save_user(
                user_id="json_user",
                name="Test",
                facts=facts,
                db_path=test_db,
            )
            user = get_user("json_user", db_path=test_db)
            assert user["facts"]["preferred_facility"] == "PHC"
            assert user["facts"]["topics"] == ["vaccination", "nutrition"]

    def test_string_facts_deserialized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            # Pass facts as a JSON string (as LLM tool would)
            save_user(
                user_id="str_facts_user",
                name="Test",
                facts='{"preferred_facility": "CHC"}',
                db_path=test_db,
            )
            user = get_user("str_facts_user", db_path=test_db)
            assert user["facts"]["preferred_facility"] == "CHC"

    def test_plain_string_facts_stored_as_note(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(
                user_id="plain_user",
                name="Test",
                facts="prefers PHC",
                db_path=test_db,
            )
            user = get_user("plain_user", db_path=test_db)
            assert user["facts"]["note"] == "prefers PHC"


class TestUpdate:
    """Tests 6-7: update and preservation of existing facts."""

    def test_update_preserves_existing_facts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(
                user_id="update_user",
                name="Sathya",
                language_preference="Telugu",
                facts={"preferred_facility": "PHC", "age_band": "30s"},
                db_path=test_db,
            )

            # Update with new fact — existing facts must survive
            updated = save_user(
                user_id="update_user",
                facts={"district": "Guntur"},
                db_path=test_db,
            )
            assert updated is not None
            assert updated["name"] == "Sathya"  # preserved
            assert updated["language_preference"] == "Telugu"  # preserved
            assert updated["facts"]["preferred_facility"] == "PHC"  # preserved
            assert updated["facts"]["age_band"] == "30s"  # preserved
            assert updated["facts"]["district"] == "Guntur"  # new

    def test_update_name_preserves_facts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(
                user_id="name_update_user",
                name="Sathya",
                facts={"preferred_facility": "PHC"},
                db_path=test_db,
            )

            updated = save_user(
                user_id="name_update_user",
                name="Sathya Kumar",
                db_path=test_db,
            )
            assert updated["name"] == "Sathya Kumar"
            assert updated["facts"]["preferred_facility"] == "PHC"


class TestDelete:
    """Tests 8: delete."""

    def test_delete_removes_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(user_id="del_user", name="ToDelete", db_path=test_db)
            assert delete_user("del_user", db_path=test_db) is True
            assert get_user("del_user", db_path=test_db) is None

    def test_delete_nonexistent_returns_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)
            assert delete_user("ghost_user", db_path=test_db) is False

    def test_double_delete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(user_id="double_del", name="Test", db_path=test_db)
            assert delete_user("double_del", db_path=test_db) is True
            assert delete_user("double_del", db_path=test_db) is False


class TestPersistence:
    """Test 10: persistence across connections."""

    def test_data_survives_separate_connections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test.db"
            init_db(test_db)

            save_user(
                user_id="persist_test",
                name="Sathya",
                language_preference="Telugu",
                facts={"preferred_facility": "PHC"},
                db_path=test_db,
            )

            # Simulate backend restart: re-read from the same db file
            user = get_user("persist_test", db_path=test_db)
            assert user is not None
            assert user["name"] == "Sathya"
            assert user["facts"]["preferred_facility"] == "PHC"
