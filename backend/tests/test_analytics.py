import unittest
from datetime import datetime, timezone
import os
import sys
from pathlib import Path

# Add src directory to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from database import (
    init_db,
    record_call_analytics,
    get_analytics_summary,
    get_connection,
)


class TestDay8Analytics(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_analytics_recording_and_summary(self):
        initial_summary = get_analytics_summary()
        initial_total = initial_summary["total_calls"]
        initial_success = initial_summary["successful_calls"]
        initial_failed = initial_summary["failed_calls"]

        # Record a SUCCESS call
        rec1 = record_call_analytics(
            call_id="voice_assistant_room_test_success",
            channel="browser",
            outcome="SUCCESS",
            language="English",
            duration_seconds=25,
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=datetime.now(timezone.utc).isoformat(),
        )
        self.assertIsNotNone(rec1)
        self.assertEqual(rec1["outcome"], "SUCCESS")

        # Record a FAILED call
        rec2 = record_call_analytics(
            call_id="voice_assistant_room_test_failed",
            channel="outbound",
            outcome="FAILED",
            language="English",
            duration_seconds=5,
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=datetime.now(timezone.utc).isoformat(),
        )
        self.assertIsNotNone(rec2)
        self.assertEqual(rec2["outcome"], "FAILED")

        # Verify summary counts
        updated_summary = get_analytics_summary()
        self.assertEqual(updated_summary["total_calls"], initial_total + 2)
        self.assertEqual(updated_summary["successful_calls"], initial_success + 1)
        self.assertEqual(updated_summary["failed_calls"], initial_failed + 1)

        # Directly verify SQL counts from DB
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM call_analytics")
            sql_total = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM call_analytics WHERE outcome='SUCCESS'"
            )
            sql_success = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome='FAILED'")
            sql_failed = cursor.fetchone()[0]

        self.assertEqual(sql_total, updated_summary["total_calls"])
        self.assertEqual(sql_success, updated_summary["successful_calls"])
        self.assertEqual(sql_failed, updated_summary["failed_calls"])


if __name__ == "__main__":
    unittest.main()
