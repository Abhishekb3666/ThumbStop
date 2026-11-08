"""Multimedia content model: reels, videos, carousels, images, audio and text posts all become a
`Content` (a hook, a timeline of consumable segments, text, topics) plus normalized 0-1 features.
Loading is the only I/O; everything else is pure and unit-tested."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import heuristics as H, video
from .demographics import CTA, EMOTION, INTERESTS, KIND_ALIASES, KINDS, LINK_CTA, NICHE_TOPICS

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")
AUDIO_EXT = (".mp3", ".wav", ".m4a")
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv")


@dataclass
class Content:
    kind: str
    hook: str
    text: str                       # everything readable/audible, used for feature detection
    segments: list                  # seconds per consumable unit (carousel slide / one block for timed media)
    topics: list = field(default_factory=list)
    caption: str = ""
    visual: float = 0.5             # 0-1 visual/production appeal; 0.5 = unknown
    hook_adjust: int = 0            # timing penalties from real video analysis (points of 100)
    pace_adjust: int = 0
    warnings: list = field(default_factory=list)
    notes: list = field(default_factory=list)   # extra issues discovered while loading

    @property
    def duration(self):
        return sum(self.segments)


def norm_kind(kind):
    k = (kind or "").lower().strip()
    k = KIND_ALIASES.get(k, k)
    if k not in KINDS:
        raise ValueError(f"unknown kind '{kind}'. Use one of: {', '.join(KINDS)}")
    return k


def detect_topics(text, declared=(), niche="general"):
    found = {}
    low = text.lower()
    for interest, kws in INTERESTS.items():
        n = sum(len(re.findall(rf"\b{re.escape(k)}\b", low)) for k in kws)
        if n:
            found[interest] = n
    top = sorted(found, key=found.get, reverse=True)[:3]
    out = list(dict.fromkeys([*declared, *NICHE_TOPICS.get(niche.lower(), []), *top]))
    return [t for t in out if t in INTERESTS]


def _words(s):
    return len(s.split())


def first_sentence(text, max_words=12):
    first = re.split(r"(?<=[.!?\n])\s", text.strip(), maxsplit=1)[0].split()
    return " ".join(first[:max_words])


def from_text(kind, text, caption="", slides=None, duration=None, topics=(), niche="general", visual=0.5):
    """Build Content from plain text. slides: list[str] for carousels."""
    kind = norm_kind(kind)
    text = text.strip()
    if kind == "carousel":
        slides = [s.strip() for s in (slides or [p for p in re.split(r"\n\s*---+\s*\n", text) if p.strip()])]
        segs = [2.0 + _words(s) / 3.5 for s in slides] or [3.0]
        hook = first_sentence(slides[0], 14) if slides else first_sentence(caption)
        body = "\n".join(slides)
    elif kind == "image":
        body = text
        segs = [3.0 + _words(text) / 4.0 + _words(caption) / 6.0]
        hook = first_sentence(text or caption)
    elif kind == "text":
        body = text
        segs = [max(3.0, _words(text) / 4.0)]
        hook = first_sentence(text)
    else:  # reel / video / audio: spoken script
        body = text
        segs = [duration if duration else max(3.0, _words(text) / H.WPS)]
        hook = first_sentence(text)
    full = (body + "\n" + caption).strip()
    return Content(kind, hook, full, segs, detect_topics(full, topics, niche), caption, visual)


def from_facts(kind, facts, topics=(), niche="general", caption=""):
    """Timed media with real transcript timings (reel/video/audio)."""
    hook, _ = video.hook_body(facts)
    text = video.script(facts)
    c = Content(norm_kind(kind), hook, (text + "\n" + caption).strip(), [max(1.0, facts.duration)],
                detect_topics(text + " " + caption, topics, niche), caption)
    hd, sd, issues = video.adjust(facts)
    c.hook_adjust, c.pace_adjust, c.notes = hd, sd, issues
    return c


def load(src, kind=None, caption="", topics=(), niche="general"):
    """Path/dir/'-' -> Content. Kind is inferred from the input when not given."""
    topics = [t.strip() for t in (topics.split(",") if isinstance(topics, str) else topics) if t.strip()]
    if src == "-":
        import sys
        return from_text(kind or "text", sys.stdin.read(), caption, topics=topics, niche=niche)
    p = Path(src)
    if p.is_dir():
        return _from_dir(p, kind, caption, topics, niche)
    ext = p.suffix.lower()
    if ext == ".json":
        return _from_spec(json.loads(p.read_text(encoding="utf-8")), kind, caption, topics, niche)
    if ext in VIDEO_EXT or ext in AUDIO_EXT:
        k = kind or ("audio" if ext in AUDIO_EXT else "reel")
        return from_facts(k, video.transcribe(str(p)), topics, niche, caption)
    if ext in IMAGE_EXT:
        return _from_images([p], "image" if not kind else kind, caption, topics, niche)
    return from_text(kind or "text", p.read_text(encoding="utf-8"), caption, topics=topics, niche=niche)


def _from_spec(spec, kind, caption, topics, niche):
    k = kind or spec.get("kind") or "text"
    slides = [s["text"] if isinstance(s, dict) else s for s in spec.get("slides", [])]
    body = spec.get("script") or spec.get("body") or spec.get("text") or ""
    c = from_text(k, body, spec.get("caption", caption), slides or None, spec.get("duration"),
                  topics or spec.get("topics", []), niche, float(spec.get("visual", 0.5)))
    if spec.get("hook"):
        c.hook = spec["hook"]
    return c


def _from_dir(d, kind, caption, topics, niche):
    imgs = sorted(f for f in d.iterdir() if f.suffix.lower() in IMAGE_EXT)
    cap = caption or next((f.read_text(encoding="utf-8") for f in d.glob("caption*.txt")), "")
    texts = sorted(d.glob("slide*.txt"))
    if texts:  # explicit slide text wins: no vision needed
        return from_text(kind or "carousel", "", cap, [t.read_text(encoding="utf-8") for t in texts], None, topics, niche)
    if not imgs:
        raise ValueError(f"{d}: no images or slide*.txt found")
    return _from_images(imgs, kind or "carousel", cap, topics, niche)


def _from_images(imgs, kind, caption, topics, niche):
    """Images have no text we can read offline: use the vision model when available, else warn."""
    from . import llm
    slides, visual, warns, tops = [], [], [], list(topics)
    for im in imgs:
        d = llm.describe_image(str(im)) if llm.available() else None
        if d:
            slides.append(d.get("text", ""))
            visual.append(float(d.get("visual", 0.5)))
            tops += d.get("topics", [])
        else:
            slides.append("")
    if not any(slides):
        warns.append("No text could be read from the image(s) (no vision model available). Add slide*.txt files "
                     "or a .json spec for a meaningful hook/clarity score; visual appeal is assumed neutral.")
    c = from_text(kind, "\n".join(slides), caption, slides if norm_kind(kind) == "carousel" else None,
                  None, tops, niche, sum(visual) / len(visual) if visual else 0.5)
    if norm_kind(kind) == "carousel" and len(imgs) > len(c.segments):
        c.segments = [3.0] * len(imgs)
    if not c.hook:
        c.hook = first_sentence(caption)
    c.warnings += warns
    return c


# ---------- features ----------

def _band(x, lo, hi, far_lo, far_hi, floor=0.25):
    if lo <= x <= hi:
        return 1.0
    if x < lo:
        return max(floor, floor + (1 - floor) * (x - far_lo) / (lo - far_lo)) if x > far_lo else floor
    return max(floor, 1 - (1 - floor) * (x - hi) / (far_hi - hi)) if x < far_hi else floor


def length_fit(c):
    d, words = c.duration, _words(c.text)
    if c.kind == "reel":
        return _band(d, 7, 35, 2, 90)
    if c.kind == "video":
        return _band(d, 20, 90, 5, 300)
    if c.kind == "audio":
        return _band(d, 20, 120, 5, 600)
    if c.kind == "carousel":
        n = len(c.segments)
        per = words / max(1, n)
        return _band(n, 5, 10, 1, 20, 0.3) * (1.0 if per <= 35 else max(0.5, 1 - (per - 35) / 80))
    if c.kind == "image":
        return min(_band(_words(c.text), 0, 25, 0, 90, 0.4), _band(_words(c.caption), 0, 150, 0, 400, 0.4))
    return _band(words, 25, 150, 3, 500, 0.3)


def sentence_ok(text):
    sents = [s for s in re.split(r"[.!?\n]+", text) if s.strip()]
    if not sents:
        return 0.6
    avg = sum(_words(s) for s in sents) / len(sents)
    return 1.0 if avg <= 18 else max(0.3, 1 - (avg - 18) / 30)


def features(c, extra_curiosity=()):
    low = c.text.lower()
    hs, hook_issues = H.hook_score(c.hook, extra_curiosity)
    hook = max(0, hs + c.hook_adjust) / 100
    clarity = max(0.0, min(1.0, 0.6 * length_fit(c) + 0.4 * sentence_ok(c.text) + c.pace_adjust / 100))
    value = min(1.0, 0.25 * bool(re.search(r"\d", c.text)) + 0.2 * bool(re.search(r"(^|\n)\s*(\d+[.)]|[-*•])|\b(step|first|second|third)\b", low))
                + 0.25 * bool(re.search(r"\bhow to\b|\bhow i\b|\bhere'?s how\b|\bsteps?\b", low))
                + 0.2 * bool(re.search(r"\b(tip|mistake|secret|framework|template|checklist|rule|hack)s?\b", low))
                + 0.1 * (_words(c.text) >= 25))
    n_emo = sum(len(re.findall(rf"\b{re.escape(w)}\b", low)) for w in EMOTION) + low.count("!")
    emotion = min(1.0, 0.2 + n_emo / max(4.0, _words(c.text) / 12))
    cta = float(any(k in low for k in CTA))
    question = float("?" in c.text)
    curiosity = 1.0 if any(w in c.hook.lower() for w in H.CURIOSITY) else 0.2
    return dict(hook=hook, clarity=clarity, value=value, emotion=emotion, cta=cta, question=question,
                curiosity=curiosity, visual=c.visual, link=float(any(k in low for k in LINK_CTA)),
                hook_issues=hook_issues)
