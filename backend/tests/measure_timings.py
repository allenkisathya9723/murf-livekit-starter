import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from agent import Assistant
from database import get_user, init_db, save_user


async def main():
    timings = {}

    # 1. Measure Database Initialization Time
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = Path(temp_dir) / "timing_test.db"
        t0 = time.perf_counter()
        init_db(test_db)
        t1 = time.perf_counter()
        timings["db_init_ms"] = (t1 - t0) * 1000.0

        # Save test user for lookup timing
        save_user(
            user_id="timing_user",
            name="Sathya",
            language_preference="Telugu",
            facts={"preferred_facility": "PHC"},
            db_path=test_db,
        )

        # 2. Measure Assistant Initialization Time
        t0 = time.perf_counter()
        assistant = Assistant(user_id="timing_user")
        t1 = time.perf_counter()
        timings["assistant_init_ms"] = (t1 - t0) * 1000.0

        # 3. Measure lookup_caller Tool Execution Time
        with patch("agent.get_user", lambda uid: get_user(uid, db_path=test_db)):
            t0 = time.perf_counter()
            _lookup_res = await assistant.lookup_caller(context=None)
            t1 = time.perf_counter()
            timings["lookup_caller_ms"] = (t1 - t0) * 1000.0

    print("=== EMPIRICAL MEASURED TIMINGS ===")
    print(f"1. Assistant initialization time: {timings['assistant_init_ms']:.2f} ms")
    print(f"2. Database initialization time: {timings['db_init_ms']:.2f} ms")
    print(f"3. lookup_caller execution time: {timings['lookup_caller_ms']:.2f} ms")


if __name__ == "__main__":
    asyncio.run(main())
