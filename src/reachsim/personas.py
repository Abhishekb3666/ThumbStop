"""Synthetic audience. hook_sens: how much the hook decides the swipe (0-1).
patience: how forgiving about pacing/length (0-1). share/follow: propensity (0-1)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    weight: float
    hook_sens: float
    patience: float
    share: float
    follow: float
    bio: str


def audience(niche: str):
    return [
        Persona("Fast scroller", 0.35, 0.95, 0.2, 0.05, 0.02, f"Swipes in 1s unless hooked; casually into {niche}."),
        Persona("Curious beginner", 0.25, 0.6, 0.6, 0.15, 0.10, f"New to {niche}, loves quick practical wins."),
        Persona("Skeptical expert", 0.10, 0.5, 0.5, 0.05, 0.05, f"Knows {niche}; hates fluff and generic advice."),
        Persona("Sharer", 0.15, 0.7, 0.5, 0.45, 0.10, f"Sends {niche} videos to friends when they feel useful or funny."),
        Persona("Loyal lurker", 0.15, 0.4, 0.8, 0.10, 0.30, f"Follows several {niche} creators; watches to the end."),
    ]
