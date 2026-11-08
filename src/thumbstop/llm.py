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
