"""Phase 2: learn from real results. History lives in $REACHSIM_HOME (default ~/.reachsim).
Weights are set proportional to each signal's rank-correlation with real engagement."""
import json
import os
from pathlib import Path

COMPONENTS = ("stop", "watch", "share", "follow")
DEFAULT = {"stop": 0.4, "watch": 0.3, "share": 0.2, "follow": 0.1}
MIN_POSTS = 5  # below this, correlations are noise; keep defaults


def home() -> Path:
    p = Path(os.environ.get("REACHSIM_HOME", Path.home() / ".reachsim"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _hist():
    f = home() / "history.json"
    return json.loads(f.read_text()) if f.exists() else {}


def _save(h):
    (home() / "history.json").write_text(json.dumps(h, indent=1))


def record(name, report):
    h = _hist()
    h.setdefault(name, {}).update(predicted=report.score, signals=report.signals())
    _save(h)


def update(name, **fields):
    h = _hist()
    if name not in h:
        raise KeyError(f"unknown post '{name}'; run analyze --save {name} first")
    h[name].update(fields)
    _save(h)


def engagement(r):
    """Engagement per viewer reached - independent of follower count."""
    reach = r.get("reach") or 0
    if not reach:
        return None
    return sum(r.get(k, 0) for k in ("likes", "comments", "shares", "saved")) / reach


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out, i = [0.0] * len(xs), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2
        i = j + 1
    return out


def spearman(a, b):
    if len(a) < 3:
        return 0.0
    ra, rb = _rank(a), _rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else 0.0


def fit():
    """Returns (weights, report dict). Writes weights.json when enough data."""
    rows = [(r, engagement(r)) for r in _hist().values() if "signals" in r]
    rows = [(r, e) for r, e in rows if e is not None]
    info = {"posts": len(rows), "score_corr": None, "component_corr": {}}
    if len(rows) < 3:
        return DEFAULT, info
    y = [e for _, e in rows]
    info["score_corr"] = round(spearman([r["predicted"] for r, _ in rows], y), 3)
    corr = {c: spearman([r["signals"][c] for r, _ in rows], y) for c in COMPONENTS}
    info["component_corr"] = {c: round(v, 3) for c, v in corr.items()}
    pos = {c: max(0.0, v) for c, v in corr.items()}
    tot = sum(pos.values())
    if len(rows) < MIN_POSTS or not tot:
        return DEFAULT, info
    # blend 50/50 with defaults so a small sample can't zero out a signal
    w = {c: round(0.5 * DEFAULT[c] + 0.5 * pos[c] / tot, 3) for c in COMPONENTS}
    (home() / "weights.json").write_text(json.dumps(w))
    info["weights"] = w
    return w, info


def weights():
    f = home() / "weights.json"
    return json.loads(f.read_text()) if f.exists() else DEFAULT
