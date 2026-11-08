"""Phase 6: trend ingestion with free public sources, no API keys.
- Google Trends daily RSS: what everyone is searching (general topics, filtered to your niche when possible)
- Reddit top-of-week for the niche's subreddits (set "subreddits" in a pack): real questions your audience asks
- Hacker News front page for the tech niche
Instagram has no public trending-audio API, so trending sounds are not covered.
Parsing is pure (unit-tested); only fetch() touches the network. Failures in one source never kill the rest."""
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from . import heuristics as H
from .personas import _find

UA = {"User-Agent": "thumbstop/0.1 (open-source content tool)"}
TEMPLATES = (
    "Everyone's talking about {t}. Here's what they miss.",
    "Stop believing the {t} hype.",
    "Why {t} matters more than you think",
    "3 things nobody tells you about {t}",
    "I tested {t} so you don't have to",
)


# mod/recurring posts that say nothing about what the audience cares about
BORING = re.compile(r"thread|megathread|weekly|daily|monthly|rant wednesday|\b20\d\d\b", re.I)


@dataclass
class Trend:
    title: str
    source: str
    weight: float = 0.0  # upvotes / traffic, only comparable within a source
    url: str = ""


def _get(url, timeout=10):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def parse_google_rss(xml_bytes):
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        t = (it.findtext("title") or "").strip()
        traffic = (it.findtext("ht:approx_traffic", namespaces=ns) or "0").replace("+", "").replace(",", "")
        if t:
            out.append(Trend(t, "google-trends", float(traffic) if traffic.isdigit() else 0.0))
    return out


def parse_reddit(atom_bytes, sub):
    """Reddit's JSON API blocks anonymous clients; the Atom feed does not. Weight = rank (top = highest)."""
    ns = "{http://www.w3.org/2005/Atom}"
    es = ET.fromstring(atom_bytes).findall(ns + "entry")
    return [Trend((e.findtext(ns + "title") or "").strip(), f"r/{sub}", float(len(es) - i),
                  (e.find(ns + "link") if e.find(ns + "link") is not None else e).get("href", ""))
            for i, e in enumerate(es) if e.findtext(ns + "title")]


def parse_hn(data):
    return [Trend(h["title"], "hacker-news", h.get("points") or 0, h.get("url") or "")
            for h in data.get("hits", []) if h.get("title")]


def _pack(niche):
    return json.loads(_find(niche).read_text(encoding="utf-8"))


def fetch(niche="general", geo="US", per_source=15):
    """Returns (trends, errors). One flaky source only adds an entry to errors."""
    pack, out, errs = _pack(niche), [], []
    jobs = [("google-trends", lambda: parse_google_rss(_get(f"https://trends.google.com/trending/rss?geo={geo}")))]
    for sub in pack.get("subreddits", []):
        jobs.append((f"r/{sub}", lambda s=sub: parse_reddit(
            _get(f"https://www.reddit.com/r/{s}/top/.rss?t=week&limit={per_source}"), s)))
    if niche.lower() == "tech":
        jobs.append(("hacker-news", lambda: parse_hn(json.loads(_get(
            f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={per_source}")))))
    for i, (name, job) in enumerate(jobs):
        if name.startswith("r/") and i > 1:
            time.sleep(2)  # Reddit answers 429 to rapid-fire anonymous requests
        try:
            out += job()[:per_source]
        except Exception as e:
            errs.append(f"{name}: {e}")
    if niche.lower() != "general":  # Google Trends is global; keep only items matching the niche
        words = {niche.lower(), *[w.lower() for w in pack.get("curiosity", [])]}
        pat = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.I)  # whole words only
        out = [t for t in out if t.source != "google-trends" or pat.search(t.title)]
    return out, errs


def ideas(trends, niche="general", n=5):
    """Candidate hooks from trends, ranked by the same hook scorer used for your scripts."""
    from .personas import load
    extra = load(niche)[1]
    cands = []
    for t in trends:
        if t.source == "google-trends":
            cands += [(s.format(t=t.title), t) for s in TEMPLATES]
        elif len(t.title.split()) <= 14 and not BORING.search(t.title):  # real audience questions work as hooks as they are
            cands.append((t.title, t))
    scored = sorted(((H.hook_score(h, extra)[0], h, t) for h, t in cands), key=lambda x: -x[0])
    seen, out = set(), []
    for s, h, t in scored:
        if t.title not in seen:  # one idea per trend so the list stays varied
            seen.add(t.title)
            out.append({"hook": h, "hook_score": s, "source": t.source, "url": t.url})
        if len(out) == n:
            break
    return out
