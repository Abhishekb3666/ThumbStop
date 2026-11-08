from dataclasses import dataclass, field

from . import heuristics as H, llm
from .personas import audience


@dataclass
class Report:
    score: int
    tier: str
    hook_score: int
    structure_score: int
    est_seconds: float
    stop_rate: float
    avg_watch: float
    share_rate: float
    follow_rate: float
    issues: list = field(default_factory=list)
    hooks: list = field(default_factory=list)
    reactions: dict = field(default_factory=dict)
    mode: str = "heuristic"


def _c(x):
    return max(0.0, min(1.0, x))


def simulate(script: str, niche: str = "general", use_llm=None) -> Report:
    hook, body = H.split(script)
    hs, hi = H.hook_score(hook)
    ss, si, dur = H.structure(script, hook, body)
    people = audience(niche)

    rx, hooks, fixes, mode = {}, [], [], "heuristic"
    if use_llm is None:
        use_llm = llm.available()
    if use_llm:
        try:
            out = llm.react(script, niche, people)
            rx, hooks, fixes, mode = out["reactions"], out["hooks"], out["fixes"], "llm"
        except Exception as e:  # network/parse failure must not kill the run
            fixes = [f"(LLM unavailable, used heuristics: {e})"]

    stop = watch = share = follow = 0.0
    for p in people:
        r = rx.get(p.name, {})
        st = _c(r.get("stops_scrolling", (hs / 100) * p.hook_sens + (1 - p.hook_sens) * 0.5 * hs / 100))
        wt = _c(r.get("watch_fraction", (ss / 100) * (0.6 + 0.4 * p.patience)))
        sh = _c(r.get("shares", st * wt * p.share * 2))
        fo = _c(r.get("follows", st * wt * p.follow * 2))
        stop += p.weight * st
        watch += p.weight * st * wt
        share += p.weight * sh
        follow += p.weight * fo
    avg_watch = watch / stop if stop else 0.0
    score = round(100 * (0.4 * stop + 0.3 * watch + 0.2 * min(1, share * 8) + 0.1 * min(1, follow * 10)))
    tier = "low" if score < 35 else "average" if score < 55 else "good" if score < 75 else "viral potential"
    return Report(score, tier, hs, ss, round(dur, 1), round(stop, 3), round(avg_watch, 3),
                  round(share, 3), round(follow, 3), hi + si + fixes, hooks,
                  {k: v.get("reason", "") for k, v in rx.items()}, mode)
