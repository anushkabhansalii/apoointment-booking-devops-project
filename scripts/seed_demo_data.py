#!/usr/bin/env python3
"""Fill SlotSync with a realistic fortnight of bookings through the public API.

Usage:
    python3 scripts/seed_demo_data.py                     # http://localhost:8000
    python3 scripts/seed_demo_data.py http://slotsync.local

Uses only the standard library so it runs anywhere Python does. Bookings
that collide with existing ones are skipped (the API answers 409).
"""

import json
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
IST = ZoneInfo("Asia/Kolkata")
random.seed(42)

CUSTOMERS = [
    "Riya Kapoor", "Arjun Nair", "Zoya Khan", "Vikram Singh", "Ananya Gupta", "Rohan Desai",
    "Ishita Bose", "Kunal Verma", "Sneha Pillai", "Aditya Joshi", "Neha Reddy", "Farhan Ali",
    "Pooja Menon", "Siddharth Rao", "Tara Fernandes", "Yash Malhotra", "Kavya Iyer", "Dev Patel",
]
# Which practitioner offers which services.
OFFERS = {
    "Aarav Mehta": ["Yoga Session", "Pilates"],
    "Diya Sharma": ["Physiotherapy"],
    "Kabir Rao": ["Deep Tissue Massage"],
    "Meera Iyer": ["Nutrition Consult"],
}
NOTES = [None, None, "First visit", "Lower back stiffness", "Prefers morning slots", "Post-surgery rehab",
         "Vegetarian meal plan", "Bring yoga mat", None]


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 - URL is chosen by the operator
        return json.loads(resp.read() or "null")


def main():
    providers = {p["name"]: p["id"] for p in call("GET", "/api/providers")}
    today = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.now(IST)
    created = skipped = 0

    for offset in range(-7, 8):
        day = today + timedelta(days=offset)
        for name, services in OFFERS.items():
            if name not in providers:
                continue
            hour = 8
            for _ in range(random.randint(2, 4)):
                hour += random.choice([1, 1, 2])
                if hour > 19:
                    break
                start = day.replace(hour=hour, minute=random.choice([0, 0, 30]))
                customer = random.choice(CUSTOMERS)
                payload = {
                    "customer_name": customer,
                    "customer_email": customer.lower().replace(" ", ".") + "@example.com",
                    "customer_phone": f"+91 9{random.randint(100000000, 999999999)}",
                    "service": random.choice(services),
                    "provider_id": providers[name],
                    "start_time": start.replace(tzinfo=None).isoformat(),
                    "notes": random.choice(NOTES),
                }
                try:
                    booking = call("POST", "/api/appointments", payload)
                except urllib.error.HTTPError as err:
                    if err.code in (409, 422):
                        skipped += 1
                        continue
                    raise
                created += 1

                if start < now:
                    status = random.choices(["completed", "no_show", "cancelled"], [8, 1, 1])[0]
                else:
                    status = random.choices(["scheduled", "confirmed", "cancelled"], [5, 4, 1])[0]
                if status != "scheduled":
                    call("PATCH", f"/api/appointments/{booking['id']}/status", {"status": status})

    print(f"Seeded {created} appointments ({skipped} skipped) at {BASE}")


if __name__ == "__main__":
    main()
