"""Crowd simulation: thousands of synthetic social-media users (age group x user type x interests x
follower/cold) each decide, with their own random draws, whether to skip, how long to stay, and what to
do (like, comment, share, save, visit profile, follow, click, hide). Aggregating them gives every
metric, per segment, before you post.

Honest limits: the priors in demographics.py are assumptions and the decision model is heuristic.
Treat numbers as relative signals (compare drafts, find weak segments); calibrate with real results.
The score compares your post to a *neutral average post* of the same kind/topic/length shown to the
same crowd with the same random draws, so 50 = average execution and 100 = double on every metric."""
import math
import random
from dataclasses import dataclass, field

from . import content as C
from .demographics import AGES, INTERESTS, PLATFORMS, USER_TYPES
from .personas import load as load_pack

KIND_TAU = dict(reel=11, video=22, audio=26, carousel=16, image=5, text=14)  # seconds of patience at avg
BASE = dict(like=.14, comment=.011, share=.030, save=.042, visit=.05, link=.02)
SCORE_W = dict(hold=.15, avg_watch=.15, completion=.15, share=.20, save=.15, like=.07, comment=.06, follow=.07)
NEUTRAL = dict(hook=.5, clarity=.7, value=.3, emotion=.3, cta=0., question=0., curiosity=.2, visual=.5, link=0.)


@dataclass
class Agent:
    age: str
    utype: str
    follower: bool
    interests: dict
    attn: float
    thr: float


@dataclass
class CrowdReport:
    kind: str
    platform: str
    n: int
    followers: float
    topics: list
    duration: float
    score: int
    tier: str
    metrics: dict
    ci: dict
    baseline: dict
    retention: list
    slide_reach: list
    segments: dict
    insights: list
    hook_issues: list
    warnings: list
    hook: str = ""
    mode: str = "crowd"

    def signals(self):  # lets `--save` / calibrate work with crowd reports
        from .simulate import signals
        m = self.metrics
        return signals(m["hold_rate"], m["avg_watch_pct"], m["share_rate"], m["follow_rate"])


def _pick(rng, weights):
    r, acc = rng.random() * sum(weights.values()), 0.0
    for k, w in weights.items():
        acc += w
        if r <= acc:
            return k
    return k


def population(n, platform, topics, followers, seed):
    plat, rng, types = PLATFORMS[platform], random.Random(seed), {k: v["share"] for k, v in USER_TYPES.items()}
    out = []
    for _ in range(n):
        age = _pick(rng, {a: w for a, w in plat["ages"].items() if w > 0})
        follower = rng.random() < followers
        ut = _pick(rng, types)
        if ut == "superfan" and not follower:
            ut = "casual"
        elif follower and rng.random() < .08:
            ut = "superfan"
        a = AGES[age]
        keyed = sorted(INTERESTS, key=lambda i: -math.log(1 - rng.random()) / (a["boost"].get(i, 1) * plat["bias"].get(i, 1)))
        interests = {i: rng.uniform(.55, 1.0) for i in keyed[:rng.randint(3, 5)]}
        if follower:  # people who follow you are into what you post about
            for t in topics[:2]:
                interests[t] = rng.uniform(.75, 1.0)
        u = USER_TYPES[ut]
        attn = 9 * a["attn"] * u["attn"] * rng.lognormvariate(0, .35) * (1.3 if follower else 1.0)
        out.append(Agent(age, ut, follower, interests, attn, u["thr"] - (.12 if follower else 0.0)))
    return out


def _sig(x):
    return 1 / (1 + math.exp(-x))


def _decide(agent, i, seed, kind, platform, f, topics, segs):
    """One agent's reaction. Seeded per agent index so a post and its baseline share random draws."""
    rng = random.Random(seed * 100003 + i)
    a, u, dur = AGES[agent.age], USER_TYPES[agent.utype], sum(segs)
    rel = max([agent.interests.get(t, 0.0) for t in topics] + [0.12]) if topics else 0.35
    fmt = min(1.2, a["fmt"][kind] * PLATFORMS[platform]["fmt"][kind])
    gate = .34 * f["hook"] + .26 * rel + .14 * min(1, fmt) + .12 * f["visual"] + .08 * f["curiosity"] + .06 * f["emotion"]
    stop = rng.random() < _sig(9 * (gate - agent.thr))
    hold = min(3.0, .5 * dur)
    drive = .4 * rel + .3 * f["clarity"] + .2 * f["hook"] + .1 * f["visual"]
    tau = KIND_TAU[kind] * agent.attn / 9 * (.4 + 1.6 * drive) * (.6 + .4 * min(1, fmt))
    t_stay = tau * (-math.log(1 - rng.random())) ** (1 / .8)
    watched = min(max(t_stay, hold), dur) if stop else rng.uniform(.2, .9) * hold
    r = dict(agent=agent, watched=watched, dur=dur, stop=stop, skip=watched < hold - 1e-9,
             completed=watched >= .95 * dur, replay=False, like=0, comment=0, share=0, save=0, visit=0,
             follow=0, link=0, hide=0)
    if not stop:
        r["hide"] = rng.random() < (.004 if rel < .2 else 0)
        return r
    e = min(1.0, watched / dur) ** .6
    q = .30 * f["hook"] + .25 * f["clarity"] + .15 * f["emotion"] + .15 * f["visual"] + .15 * f["value"]
    relmod = .4 + .8 * rel
    d = dict(like=q, comment=.4 * f["cta"] + .3 * f["question"] + .3 * f["emotion"],
             share=.4 * f["emotion"] + .3 * rel + .3 * f["value"], save=.6 * f["value"] + .2 * f["clarity"] + .2 * rel,
             visit=.5 * rel + .5 * f["hook"])
    mult = dict(like=u["like"] * a["like"], comment=u["comment"] * a["comment"], share=u["share_"] * a["share"],
                save=u["save"] * a["save"], visit=1.0)
    for k in ("like", "comment", "share", "save", "visit"):
        r[k] = rng.random() < min(.95, BASE[k] * mult[k] * (.4 + 1.2 * d[k]) * e * relmod)
    if f["link"]:
        r["link"] = rng.random() < min(.5, BASE["link"] * (.4 + 1.2 * rel) * e)
    if r["visit"] and not agent.follower:
        r["follow"] = rng.random() < min(.9, .14 * u["follow"] * a["follow"] * (.5 + q))
    if r["completed"] and dur <= 45 and kind in ("reel", "video", "audio"):
        r["replay"] = rng.random() < min(.5, .25 * f["emotion"] + .2 * rel)
    if watched / dur < .35 and rel < .3:
        r["hide"] = rng.random() < .03
    return r


def _agg(rows):
    n = len(rows) or 1
    viewers = [r for r in rows if r["stop"]]
    nv = len(viewers) or 1
    s = lambda k: sum(1 for r in rows if r[k]) / n
    m = dict(
        skip_rate=s("skip"), hold_rate=1 - s("skip"),
        avg_watch_pct=sum(min(1, r["watched"] / r["dur"]) for r in rows) / n,
        avg_watch_pct_viewers=sum(min(1, r["watched"] / r["dur"]) for r in viewers) / nv,
        avg_watch_seconds=sum(r["watched"] for r in rows) / n,
        completion_rate=s("completed"), replay_rate=s("replay"),
        like_rate=s("like"), comment_rate=s("comment"), share_rate=s("share"), save_rate=s("save"),
        profile_visit_rate=s("visit"), follow_rate=s("follow"), link_click_rate=s("link"),
        not_interested_rate=s("hide"),
    )
    m["engagement_rate"] = m["like_rate"] + m["comment_rate"] + m["share_rate"] + m["save_rate"]
    return m


def _score(m, base):
    pairs = dict(hold=("hold_rate",), avg_watch=("avg_watch_pct",), completion=("completion_rate",), share=("share_rate",),
                 save=("save_rate",), like=("like_rate",), comment=("comment_rate",), follow=("follow_rate",))
    tot = 0.0
    for k, (mk,) in pairs.items():
        ratio = m[mk] / base[mk] if base[mk] > 1e-9 else 1.0
        tot += SCORE_W[k] * min(ratio, 2.0) * 50
    return round(tot)


def _tier(score):
    return "low" if score < 35 else "average" if score < 55 else "good" if score < 75 else "viral potential"


def _curve(rows, segs):
    dur = sum(segs)
    w = [r["watched"] for r in rows]
    n = len(w) or 1
    timed = [{"at": f"{q}%", "seconds": round(dur * q / 100, 1), "pct": sum(x >= dur * q / 100 - 1e-9 for x in w) / n}
             for q in range(10, 101, 10)]
    reach, start = [], 0.0
    for i, sg in enumerate(segs):
        reach.append({"slide": i + 1, "pct": 1.0 if i == 0 else sum(x > start for x in w) / n})
        start += sg
    return timed, reach


def _segments(rows):
    out = {}
    for name, key in (("age", lambda r: r["agent"].age), ("user_type", lambda r: r["agent"].utype),
                      ("audience", lambda r: "followers" if r["agent"].follower else "cold feed"),
                      ("interest", lambda r: max(r["agent"].interests, key=r["agent"].interests.get))):
        groups = {}
        for r in rows:
            groups.setdefault(key(r), []).append(r)
        out[name] = {}
        for label, g in sorted(groups.items()):
            if len(g) >= 20:
                m = _agg(g)
                out[name][label] = {"n": len(g), **{k: round(m[k], 4) for k in (
                    "skip_rate", "avg_watch_pct", "completion_rate", "like_rate", "comment_rate", "share_rate", "save_rate", "follow_rate")}}
    return out


def _insights(c, f, m, base, retention, slide_reach, segs, platform):
    out = []
    pct = lambda x: f"{x:.0%}"
    if m["skip_rate"] >= .55:
        out.append(f"{pct(m['skip_rate'])} of viewers skip before the {'3s' if c.duration > 6 else 'first beat'}: the hook is the main problem.")
    ages = {k: v for k, v in segs.get("age", {}).items() if v["n"] >= 40}
    if len(ages) >= 2:
        best, worst = min(ages, key=lambda k: ages[k]["skip_rate"]), max(ages, key=lambda k: ages[k]["skip_rate"])
        if ages[worst]["skip_rate"] - ages[best]["skip_rate"] >= .15:
            out.append(f"Resonates with {best} (skip {pct(ages[best]['skip_rate'])}) but loses {worst} (skip {pct(ages[worst]['skip_rate'])}).")
    aud = segs.get("audience", {})
    if "followers" in aud and "cold feed" in aud and aud["cold feed"]["skip_rate"] - aud["followers"]["skip_rate"] >= .25:
        out.append("Works for people who already follow you but not for strangers: the hook relies on context new viewers lack.")
    if len(c.segments) > 1 and slide_reach:
        drops = [(slide_reach[i]["pct"] - slide_reach[i + 1]["pct"], i + 2) for i in range(len(slide_reach) - 1)]
        d, at = max(drops)
        if d >= .12:
            out.append(f"Biggest drop-off is at slide {at} ({pct(d)} of viewers leave): tighten or reorder around it.")
    elif retention:
        drops = [(retention[i]["pct"] - retention[i + 1]["pct"], i) for i in range(len(retention) - 1)]
        d, i = max(drops)
        if d >= .08 and c.duration > 6:
            out.append(f"Biggest retention cliff between {retention[i]['seconds']}s and {retention[i + 1]['seconds']}s: re-hook or cut there.")
    if f["cta"] == 0:
        out.append("No call to action: add 'save this' / 'send to a friend' / a question to lift saves, shares and comments.")
    if f["value"] < .35 and m["save_rate"] < base["save_rate"] * 1.1:
        out.append("Low save-worthiness: add concrete numbers, steps or a checklist people want to keep.")
    if f["question"] == 0 and m["comment_rate"] < base["comment_rate"] * 1.1:
        out.append("Nothing invites a reply: end with a direct question or a take people can disagree with.")
    ff = PLATFORMS[platform]["fmt"][c.kind]
    if ff < .5:
        out.append(f"{c.kind} is a weak format on {platform} (native formats do far better); consider reworking it.")
    if not c.topics:
        out.append("Couldn't detect a topic; pass --topics (e.g. fitness,health) so interest matching is meaningful.")
    return out


def run(c, platform="instagram", n=1000, followers=0.25, seed=7, niche="general"):
    """Simulate `n` users seeing content `c`. Deterministic for a given seed."""
    if platform not in PLATFORMS:
        raise ValueError(f"unknown platform '{platform}'. Use one of: {', '.join(PLATFORMS)}")
    extra = load_pack(niche)[1]
    f = C.features(c, extra)
    pop = population(n, platform, c.topics, followers, seed)
    rows = [_decide(a, i, seed, c.kind, platform, f, c.topics, c.segments) for i, a in enumerate(pop)]
    nf = {**NEUTRAL, "hook": .5, "visual": c.visual}
    base_rows = [_decide(a, i, seed, c.kind, platform, nf, c.topics, c.segments) for i, a in enumerate(pop)]
    m, base = _agg(rows), _agg(base_rows)
    se = lambda p: round(1.96 * math.sqrt(max(p * (1 - p), 0) / n), 4)
    ci = {k: se(v) for k, v in m.items() if k.endswith("_rate") or k == "avg_watch_pct"}
    retention, reach = _curve(rows, c.segments)
    segs = _segments(rows)
    score = _score(m, base)
    return CrowdReport(c.kind, platform, n, followers, c.topics, round(c.duration, 1), score, _tier(score),
                       {k: round(v, 4) for k, v in m.items()}, ci, {k: round(v, 4) for k, v in base.items()},
                       [{**p, "pct": round(p["pct"], 4)} for p in retention],
                       [{**p, "pct": round(p["pct"], 4)} for p in reach] if len(c.segments) > 1 else [],
                       segs, _insights(c, f, m, base, retention, reach, segs, platform),
                       f["hook_issues"] + c.notes, c.warnings, c.hook)


def rank_hooks(c, hooks, **kw):
    """Re-run the same crowd with each alternative hook; shows which actually lowers the skip rate."""
    import copy
    base = run(c, **kw)
    out = [{"hook": c.hook, "score": base.score, "skip_rate": base.metrics["skip_rate"], "current": True}]
    for h in hooks:
        c2 = copy.copy(c)
        c2.hook = h
        r = run(c2, **kw)
        out.append({"hook": h, "score": r.score, "skip_rate": r.metrics["skip_rate"], "current": False})
    return sorted(out, key=lambda x: -x["score"])
