"""Posting calendar: rotates proven short-form content pillars so the feed stays varied."""
from datetime import date, timedelta

PILLARS = [
    ("Myth-bust", "Stop doing X - here's why it's wrong"),
    ("Quick win", "N-second fix for a common problem"),
    ("Story / result", "I did X for 30 days - here's what happened"),
    ("List", "3 things I wish I knew before Y"),
    ("Reaction / trend", "Take on something trending in your niche"),
    ("Behind the scenes", "How I actually do X (no filter)"),
    ("Q&A / comment reply", "Answer a real follower question"),
]


def plan(niche: str, days: int = 7, per_day: int = 1, start: date = None):
    start = start or date.today()
    slots = ("19:00", "12:00", "08:00")[:per_day]  # ponytail: static times; tune from insights()
    out, i = [], 0
    for d in range(days):
        for t in slots:
            name, tmpl = PILLARS[i % len(PILLARS)]
            out.append({"date": str(start + timedelta(days=d)), "time": t, "pillar": name,
                        "idea": f"[{niche}] {tmpl}"})
            i += 1
    return out
