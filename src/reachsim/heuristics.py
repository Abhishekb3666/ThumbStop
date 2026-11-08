"""Offline, deterministic scoring of a short-form script. No API key needed."""
import re

WPS = 2.6  # spoken words per second
GREETINGS = ("hey guys", "hi guys", "hi everyone", "hey everyone", "welcome back",
             "hello everyone", "so today", "in this video", "today i", "today we")
CURIOSITY = ("secret", "mistake", "nobody", "never", "stop", "wrong", "truth", "why",
             "how", "without", "before you", "worst", "best", "only", "hack", "myth")
CTA = ("follow", "comment", "share", "save", "send this", "link in bio", "subscribe")


def split(script: str):
    """Return (hook, body). Hook = the first ~3 seconds of speech (~8 words / first sentence)."""
    words = script.split()
    first = re.split(r"(?<=[.!?\n])\s", script.strip(), maxsplit=1)[0].split()
    hook = " ".join(first[:12] if len(first) > 12 else first)
    return hook, " ".join(words[len(hook.split()):])


def hook_score(hook: str):
    """0-100 plus a list of issues."""
    h, issues, s = hook.lower(), [], 40
    n = len(hook.split())
    if any(h.startswith(g) for g in GREETINGS):
        s -= 25; issues.append("Hook opens with a greeting/intro - viewers swipe in the first second.")
    if n > 12:
        s -= 10; issues.append(f"Hook is {n} words; aim for 12 or fewer (about 3 seconds).")
    elif n <= 9:
        s += 8
    if re.search(r"\d", hook):
        s += 12
    else:
        issues.append("No number or concrete result in the hook - specifics stop the scroll.")
    if "?" in hook:
        s += 8
    if re.search(r"\byou(r)?\b", h):
        s += 10
    else:
        issues.append("Hook never addresses the viewer ('you') directly.")
    if any(w in h for w in CURIOSITY):
        s += 18
    else:
        issues.append("No curiosity gap or tension - promise a payoff the viewer must watch to get.")
    return max(0, min(100, s)), issues


def structure(script: str, hook: str, body: str, dur: float = None):
    """Retention/shareability score 0-100 plus issues and estimated duration."""
    words = len(script.split())
    dur = dur or words / WPS
    s, issues = 50, []
    if dur < 8:
        s -= 10; issues.append("Under 8s: too short to deliver value or earn a follow.")
    elif dur <= 35:
        s += 15
    elif dur <= 60:
        s -= 5; issues.append(f"~{dur:.0f}s is long; cut to under 35s unless every line earns its place.")
    else:
        s -= 20; issues.append(f"~{dur:.0f}s is very long for short-form; split into a series.")
    sentences = [x for x in re.split(r"[.!?\n]+", body) if x.strip()]
    if sentences:
        avg = sum(len(x.split()) for x in sentences) / len(sentences)
        if avg > 18:
            s -= 10; issues.append("Long sentences - tighten to punchy lines for pacing.")
        else:
            s += 8
    if any(c in script.lower() for c in CTA):
        s += 10
    else:
        issues.append("No call to action (follow / save / send to a friend).")
    return max(0, min(100, s)), issues, dur
