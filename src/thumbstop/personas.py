"""Audience personas come from JSON packs: ~/.thumbstop/packs/<niche>.json (yours) overrides
the built-in src/thumbstop/packs/<niche>.json; unknown niches use default.json.
hook_sens: how much the hook decides the swipe (0-1). patience: pacing forgiveness (0-1).
share/follow: propensity (0-1). Optional "curiosity": extra hook trigger words for the niche."""
import json
from dataclasses import dataclass
from pathlib import Path

from .calibrate import home

BUILTIN = Path(__file__).parent / "packs"
FIELDS = ("name", "weight", "hook_sens", "patience", "share", "follow", "bio")


@dataclass(frozen=True)
class Persona:
    name: str
    weight: float
    hook_sens: float
    patience: float
    share: float
    follow: float
    bio: str


def _find(niche: str):
    key = niche.lower().strip().replace(" ", "-")
    for d in (home() / "packs", BUILTIN):
        if (d / f"{key}.json").exists():
            return d / f"{key}.json"
    return BUILTIN / "default.json"


def load(niche: str):
    """Returns (personas, extra_curiosity_words). Weights are normalized; bad packs raise ValueError."""
    path = _find(niche)
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("personas") or []
    if not raw:
        raise ValueError(f"{path}: no personas")
    for p in raw:
        miss = [f for f in FIELDS if f not in p]
        if miss:
            raise ValueError(f"{path}: persona {p.get('name', '?')} missing {miss}")
        if not all(0 <= p[f] <= 1 for f in FIELDS[2:6]):
            raise ValueError(f"{path}: {p['name']} values must be within 0-1")
    total = sum(p["weight"] for p in raw)
    people = [Persona(**{**p, "weight": p["weight"] / total, "bio": p["bio"].format(niche=niche)}) for p in raw]
    return people, [w.lower() for w in data.get("curiosity", [])]


def audience(niche: str):
    return load(niche)[0]


def available():
    names = {f.stem for d in (BUILTIN, home() / "packs") if d.exists() for f in d.glob("*.json")}
    return sorted(names - {"default"})
