"""Video input. Transcription needs `pip install thumbstop[video]` (faster-whisper decodes via PyAV,
so no system ffmpeg is required). Everything after transcribe() is pure logic and unit-tested."""
from dataclasses import dataclass

VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".mp3", ".wav", ".m4a")


@dataclass
class Facts:
    duration: float
    segments: list  # [(start_s, end_s, text)]


def transcribe(path: str, model: str = "base") -> Facts:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("Video input needs: pip install thumbstop[video]")
    segs, info = WhisperModel(model, compute_type="int8").transcribe(path)
    return Facts(info.duration, [(s.start, s.end, s.text.strip()) for s in segs])


def script(f: Facts) -> str:
    return " ".join(t for _, _, t in f.segments)


def hook_body(f: Facts, window: float = 3.0):
    """Hook = what is actually spoken in the first `window` seconds (finish the first segment's words)."""
    first = [t for s, _, t in f.segments if s < window]
    hook = " ".join(first[:1]) if first else ""
    rest = [t for s, _, t in f.segments if s >= window] + first[1:]
    return hook, " ".join(rest)


def adjust(f: Facts):
    """(hook_delta, structure_delta, issues) from timing facts a transcript alone can't show."""
    hd = sd = 0
    issues = []
    if not f.segments:
        return -40, -40, ["No speech detected - add a spoken or on-screen text hook."]
    start = f.segments[0][0]
    if start > 1.0:
        hd -= 15
        issues.append(f"Nothing is said for the first {start:.1f}s - start talking/showing the payoff at 0s.")
    gaps = [b[0] - a[1] for a, b in zip(f.segments, f.segments[1:])]
    dead = [g for g in gaps if g > 1.5]
    if dead:
        sd -= 5 * len(dead)
        issues.append(f"{len(dead)} pause(s) over 1.5s (longest {max(dead):.1f}s) - cut dead air.")
    spoken = sum(len(t.split()) for _, _, t in f.segments)
    wps = spoken / max(1.0, f.segments[-1][1] - start)
    if wps < 1.8:
        sd -= 8
        issues.append(f"Slow delivery ({wps:.1f} words/s) - tighten pacing.")
    elif wps > 3.8:
        sd -= 5
        issues.append(f"Very fast delivery ({wps:.1f} words/s) - viewers may not keep up.")
    return hd, sd, issues
