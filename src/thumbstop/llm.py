"""Optional LLM layer: personas react like real viewers and we get rewritten hooks.
Needs `pip install thumbstop[llm]` and ANTHROPIC_API_KEY. Falls back to heuristics otherwise."""
import json
import os

MODEL = os.environ.get("THUMBSTOP_MODEL", "claude-sonnet-5-5")


def available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def react(script: str, niche: str, personas, platform: str = "Instagram Reels"):
    """Return {"reactions": {persona_name: {...}}, "hooks": [str], "fixes": [str]}."""
    import anthropic
    people = "\n".join(f"- {p.name}: {p.bio}" for p in personas)
    prompt = f"""You simulate viewers of a {platform} video in the niche "{niche}".
Script (first line is the hook):
\"\"\"{script}\"\"\"

Viewers:
{people}

For each viewer decide honestly (be harsh; most viewers swipe): stops_scrolling (0-1 probability),
watch_fraction (0-1), shares (0-1), follows (0-1), and a one-line reason.
Then write 5 stronger hooks (<=12 words, same topic) and 3 concrete fixes.
Reply with ONLY JSON: {{"reactions": {{"<name>": {{"stops_scrolling":0,"watch_fraction":0,"shares":0,"follows":0,"reason":""}}}}, "hooks": [], "fixes": []}}"""
    msg = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=1500, messages=[{"role": "user", "content": prompt}])
    text = msg.content[0].text
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def _json(text):
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def describe_image(path: str):
    """Vision pass for image/carousel files: on-image text, topics and visual appeal. None on any failure."""
    import base64
    import mimetypes
    try:
        import anthropic
        from .demographics import INTERESTS
        mt = mimetypes.guess_type(path)[0] or "image/jpeg"
        data = base64.standard_b64encode(open(path, "rb").read()).decode()
        ask = ("This is one image/slide of a social media post. Reply ONLY with JSON: "
               '{"text": "<all text visible in the image, verbatim>", "topics": [<up to 3 from: '
               + ", ".join(INTERESTS) + '>], "visual": <0-1 how scroll-stopping and well-produced it looks>}')
        content = [{"type": "image", "source": {"type": "base64", "media_type": mt, "data": data}},
                   {"type": "text", "text": ask}]
        msg = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=500, messages=[{"role": "user", "content": content}])
        return _json(msg.content[0].text)
    except Exception:
        return None


def hooks(text: str, niche: str, kind: str, n: int = 5):
    """Alternative opening lines to be re-scored by the crowd. [] when unavailable."""
    try:
        import anthropic
        msg = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=600, messages=[{"role": "user", "content":
            f'Write {n} stronger opening hooks (max 12 words each, same topic and promise) for this {kind} post in the '
            f'"{niche}" niche. Reply ONLY with JSON {{"hooks": []}}.\n\n"""{text[:3000]}"""'}])
        return _json(msg.content[0].text)["hooks"][:n]
    except Exception:
        return []
