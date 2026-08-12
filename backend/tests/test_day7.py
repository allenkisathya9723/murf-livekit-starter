import os
import sys
import unittest
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from database import init_db, save_escalation, get_escalations, get_escalation, DEFAULT_DB_PATH
from agent import Assistant

class TestDay7Escalations(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_database_schema_and_save(self):
        """Test creating an escalation record in SQLite database"""
        res = save_escalation(
            reason="Diagnosis requested",
            summary="Caller asked if symptoms indicate dengue.",
            what_checked="Agent provided safety guidance and refused diagnosis.",
            urgency="Medium",
            language="English",
            preferred_follow_up="Phone",
            caller_id="test_caller_123"
        )
        self.assertIsNotNone(res)
        self.assertTrue(res["reference_id"].startswith("JM-"))
        self.assertEqual(res["reason"], "Diagnosis requested")
        self.assertEqual(res["status"], "OPEN")

        # Retrieve all escalations
        all_esc = get_escalations()
        self.assertGreaterEqual(len(all_esc), 1)
        found = any(e["reference_id"] == res["reference_id"] for e in all_esc)
        self.assertTrue(found)

    def test_create_escalation_tool_permission_yes(self):
        """Test tool execution when user_consented=True"""
        assistant = Assistant(user_id="test_user_consent", ctx=None)
        # Call tool with permission
        import asyncio
        result = asyncio.run(
            assistant.create_escalation(
                context=None,
                reason="Red-flag symptom reported",
                summary="Caller reported severe chest pain.",
                what_checked="Advised emergency hospital visit immediately.",
                user_consented=True,
                urgency="Critical",
                language="English"
            )
        )
        self.assertIn("Successfully created human escalation request", result)
        self.assertIn("Reference ID is JM-", result)

    def test_create_escalation_tool_permission_no(self):
        """Test tool execution when user_consented=False"""
        assistant = Assistant(user_id="test_user_no_consent", ctx=None)
        import asyncio
        result = asyncio.run(
            assistant.create_escalation(
                context=None,
                reason="Diagnosis requested",
                summary="User asked for diagnosis.",
                what_checked="Refused diagnosis.",
                user_consented=False
            )
        )
        self.assertIn("ERROR: Cannot create human help request without explicit user consent", result)

if __name__ == "__main__":
    unittest.main()
