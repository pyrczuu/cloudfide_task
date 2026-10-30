from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKINGS_FILE = ROOT / "data" / "bookings.json"
POLICIES_DIR = ROOT / "data" / "policies"

DATE_NOW = datetime(2026, 6, 10, 9, 0, tzinfo=timezone(timedelta(hours=2)))