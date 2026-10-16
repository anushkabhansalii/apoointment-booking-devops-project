"""The studio's service menu.

Kept in code rather than the database: it changes with a release, not at
runtime, and the frontend reads it from GET /api/services.
"""

import os
from zoneinfo import ZoneInfo

STUDIO_TZ = ZoneInfo(os.getenv("STUDIO_TZ", "Asia/Kolkata"))

SERVICES: dict[str, dict] = {
    "Yoga Session": {"duration": 60, "price": 900},
    "Physiotherapy": {"duration": 45, "price": 1500},
    "Nutrition Consult": {"duration": 30, "price": 1200},
    "Deep Tissue Massage": {"duration": 60, "price": 2200},
    "Pilates": {"duration": 50, "price": 1100},
}
