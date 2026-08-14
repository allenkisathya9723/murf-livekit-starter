from pathlib import Path
import sys
import unittest

# Add src directory to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from agent import (  # noqa: E402
    SPECIALIST_SYSTEM_PROMPT,
    Assistant,
    ClinicAppointmentSpecialist,
)
from database import init_db  # noqa: E402


class TestDay9Handoff(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_specialist_agent_structure(self):
        specialist = ClinicAppointmentSpecialist(user_id="test_user", ctx=None)
        self.assertEqual(specialist.instructions, SPECIALIST_SYSTEM_PROMPT)
        self.assertTrue(specialist.is_successful)

    def test_handoff_tool_registration(self):
        assistant = Assistant(user_id="test_user", ctx=None)
        # Check if transfer_to_clinic_specialist is in assistant's tools list
        tool_names = [tool.info.name for tool in assistant.tools]
        self.assertIn("transfer_to_clinic_specialist", tool_names)

    def test_normal_path_no_handoff(self):
        assistant = Assistant(user_id="test_user", ctx=None)
        # Verify get_health_camp_schedule is present for normal health camp path
        tool_names = [tool.info.name for tool in assistant.tools]
        self.assertIn("get_health_camp_schedule", tool_names)


if __name__ == "__main__":
    unittest.main()
