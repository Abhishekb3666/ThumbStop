import json
import random

import pytest

from thumbstop import content as C, crowd, heuristics as H
from thumbstop.cli import main
from thumbstop.demographics import KINDS, PLATFORMS

WORDS = ("stop gym money recipe 3 5 100 why how you never secret mistake save follow ai app 🔥 मैं 你好 ? ! . , - — "
         "ÿ 'quote' \"dq\" <b>x</b> & % $ # @ /// \\\\ \t").split()


def rand_text(rng):
    n = rng.choice([0, 1, 2, 5, 30, 200, 1500])
    return " ".join(rng.choice(WORDS) for _ in range(n)) if rng.random() < .9 else rng.choice(["", " ", "\n\n", "...", "?!", "🔥" * 50])


def test_fuzz_invariants():
    rng = random.Random(11)
    for _ in range(250):
        kind, platform = rng.choice(KINDS), rng.choice(list(PLATFORMS))
        text = rand_text(rng)
        slides = [rand_text(rng) for _ in range(rng.randint(0, 12))] if kind == "carousel" else None
        c = C.from_text(kind, text, caption=rand_text(rng), slides=slides, duration=rng.choice([None, 0.5, 5, 600]))
        r = crowd.run(c, platform=platform, n=rng.choice([50, 120, 300]), followers=rng.random(), seed=rng.randint(1, 999),
                      niche=rng.choice(["general", "fitness", "tech", "weird niche"]))
        assert isinstance(r.score, int) and 0 <= r.score <= 100
        m = r.metrics
        assert all(0 <= v <= 1 for k, v in m.items() if k.endswith("_rate") or k.startswith("avg_watch_pct"))
        assert m["completion_rate"] <= m["hold_rate"] + 1e-9 and m["follow_rate"] <= m["profile_visit_rate"] + 1e-9
        assert m["avg_watch_pct_viewers"] >= 0 and m["engagement_rate"] >= 0
        pts = [p["pct"] for p in r.retention]
        assert pts == sorted(pts, reverse=True)
        json.dumps(r.__dict__)  # must be serializable for --json and the web API


def test_spelled_numbers_count_in_hooks():
    assert H.hook_score("Three tips for a better workout")[0] > H.hook_score("Some tips for a better workout")[0]


def test_cta_helps_saves_and_shares():
    base = "Most people lift wrong. Here is how to fix your squat with simple cues and good form for better results over time."
    kw = dict(n=3000, niche="fitness")
    a = crowd.run(C.from_text("reel", base, niche="fitness"), **kw).metrics
    b = crowd.run(C.from_text("reel", base + " Save this and send this to a friend.", niche="fitness"), **kw).metrics
    assert b["save_rate"] > a["save_rate"] and b["share_rate"] > a["share_rate"]


def test_length_outside_ideal_band_is_penalized():
    base = "Most people lift wrong. Here is how to fix your squat with simple cues and good form for better results over time."
    ok = crowd.run(C.from_text("reel", base, niche="fitness"), n=2000, niche="fitness").score
    long = crowd.run(C.from_text("reel", " ".join([base] * 8), niche="fitness"), n=2000, niche="fitness").score
    assert long < ok - 5


@pytest.mark.parametrize("kw", [dict(n=0), dict(n=10), dict(n=10**7), dict(followers=-1), dict(followers=2), dict(platform="myspace")])
def test_bad_parameters_raise_clean_errors(kw):
    with pytest.raises(ValueError):
        crowd.run(C.from_text("reel", "hello there friends"), **kw)


def test_cli_user_errors_are_one_clean_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    empty = tmp_path / "e.txt"
    empty.write_text("   ")
    ok = tmp_path / "ok.txt"
    ok.write_text("Stop wasting 3 hours on this gym mistake.")
    for argv in (["crowd", str(tmp_path / "nope.txt")], ["crowd", str(empty), "--kind", "reel"],
                 ["crowd", str(ok), "--kind", "hologram"], ["crowd", str(ok), "--kind", "reel", "-n", "0"],
                 ["crowd", str(ok), "--platform", "myspace"], ["result", "ghost", "reach=1"]):
        with pytest.raises(SystemExit) as e:
            main(argv)
        assert str(e.value).startswith("thumbstop: error:") and "Traceback" not in str(e.value)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(SystemExit):
        main(["crowd", str(bad)])


def test_cli_hooks_without_llm_prints_note(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    f = tmp_path / "s.txt"
    f.write_text("Stop wasting 3 hours on this gym mistake. Follow for more.")
    main(["crowd", str(f), "--kind", "reel", "--hooks", "-n", "100"])
    assert "--hooks needs" in capsys.readouterr().err


def test_web_api_abuse(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    from api.crowd import run
    xss = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
    code, out = run({"kind": "text", "text": xss, "topics": xss, "niche": xss})
    assert code == 200
    json.dumps(out)
    for bad in ({"text": None}, {"text": 5}, {"text": "x", "followers": "abc"}, {"text": "x", "n": "lots"}, {"text": "x", "kind": 7}):
        code, out = run(bad)
        assert code in (200, 400)  # must never raise
    assert run({"text": "x", "followers": 99})[0] == 200 and run({"text": "x", "followers": 99})[1]["followers"] == 1.0
