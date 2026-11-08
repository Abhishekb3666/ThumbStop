import json

import pytest

from thumbstop import calibrate, content as C, crowd

GOOD = ("Stop wasting 3 hours a day on this gym mistake. Most people never fix it. "
        "Do 3 sets, rest 60 seconds, and track every rep. Follow for more.")
BAD = ("Hey guys welcome back to my channel so today I am going to talk about something kind of interesting "
       "about the gym and how people work out in general and I hope you enjoy this video thanks for watching")
SLIDES = ["5 gym mistakes killing your gains", "1. Skipping warm-ups", "2. Ego lifting", "3. No tracking", "Save this and send it to a friend"]


def run(c, **kw):
    kw.setdefault("niche", "fitness")
    kw.setdefault("n", 800)
    return crowd.run(c, **kw)


def test_deterministic_and_seed_matters():
    c = C.from_text("reel", GOOD, niche="fitness")
    assert run(c).metrics == run(c).metrics
    assert run(c, seed=1).metrics != run(c, seed=2).metrics


def test_better_hook_means_fewer_skips_and_higher_score():
    g, b = run(C.from_text("reel", GOOD, niche="fitness")), run(C.from_text("reel", BAD, niche="fitness"))
    assert g.metrics["skip_rate"] < b.metrics["skip_rate"] and g.score > b.score


def test_every_format_runs_with_sane_metrics():
    cs = [C.from_text("reel", GOOD, niche="fitness"), C.from_text("video", GOOD * 4, niche="fitness"),
          C.from_text("audio", GOOD * 3, niche="fitness"), C.from_text("carousel", "", slides=SLIDES, niche="fitness"),
          C.from_text("image", "5 gym mistakes", caption="Save this", niche="fitness"),
          C.from_text("text", "Hot take: you don't need a gym. What do you think?", niche="fitness")]
    for c in cs:
        r = run(c)
        assert 0 <= r.score <= 100 and r.kind == c.kind
        assert all(0 <= v <= 1 for k, v in r.metrics.items() if k.endswith("_rate") or k.startswith("avg_watch_pct"))
        assert r.metrics["completion_rate"] <= r.metrics["hold_rate"] + 1e-9
        assert r.metrics["follow_rate"] <= r.metrics["profile_visit_rate"] + 1e-9


def test_carousel_reach_is_monotonic_and_segments_add_up():
    r = run(C.from_text("carousel", "", slides=SLIDES, niche="fitness"))
    pcts = [s["pct"] for s in r.slide_reach]
    assert pcts[0] == 1.0 and len(pcts) == len(SLIDES) and pcts == sorted(pcts, reverse=True)
    assert sum(v["n"] for v in r.segments["audience"].values()) == r.n
    retention = [p["pct"] for p in run(C.from_text("reel", GOOD, niche="fitness")).retention]
    assert retention == sorted(retention, reverse=True)


def test_followers_stay_longer_than_cold_feed():
    seg = run(C.from_text("reel", GOOD, niche="fitness"), followers=0.4).segments["audience"]
    assert seg["followers"]["skip_rate"] < seg["cold feed"]["skip_rate"]


def test_platform_changes_outcomes():
    c = C.from_text("text", "Hot take: most gyms are a scam. What do you think?", niche="fitness")
    assert run(c, platform="x").metrics["skip_rate"] < run(c, platform="tiktok").metrics["skip_rate"]
    with pytest.raises(ValueError):
        run(c, platform="myspace")


def test_loaders(tmp_path):
    spec = tmp_path / "p.json"
    spec.write_text(json.dumps({"kind": "carousel", "slides": SLIDES, "caption": "Which one are you?", "topics": ["fitness"]}))
    c = C.load(str(spec))
    assert c.kind == "carousel" and len(c.segments) == 5 and "fitness" in c.topics
    d = tmp_path / "slides"
    d.mkdir()
    for i, s in enumerate(SLIDES):
        (d / f"slide{i + 1}.txt").write_text(s)
    (d / "caption.txt").write_text("Which one are you?")
    assert C.load(str(d)).kind == "carousel" and len(C.load(str(d)).segments) == 5
    md = tmp_path / "t.md"
    md.write_text("Why your squat stalls. Fix it.")
    assert C.load(str(md)).kind == "text" and C.load(str(md), kind="short").kind == "reel"
    with pytest.raises(ValueError):
        C.norm_kind("hologram")


def test_images_without_vision_warn(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    (tmp_path / "a.png").write_bytes(b"x")
    c = C.load(str(tmp_path), kind="carousel")
    assert c.warnings and run(c).warnings


def test_rank_hooks_and_calibration(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    c = C.from_text("reel", BAD, niche="fitness")
    ranked = crowd.rank_hooks(c, ["Stop wasting 3 hours on this gym mistake", "hey guys welcome back"], niche="fitness", n=800)
    assert [r["score"] for r in ranked] == sorted((r["score"] for r in ranked), reverse=True)
    assert ranked[0]["hook"].startswith("Stop wasting") and any(r["current"] for r in ranked)
    calibrate.record("x", run(c))
    assert calibrate._hist()["x"]["predicted"] == run(c).score


def test_cli_crowd(tmp_path, monkeypatch, capsys):
    from thumbstop.cli import main
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    f = tmp_path / "s.txt"
    f.write_text(GOOD)
    main(["crowd", str(f), "--kind", "reel", "--niche", "fitness", "-n", "500"])
    out = capsys.readouterr().out
    assert "CROWD SCORE" in out and "skip rate" in out and "By age" in out
    main(["crowd", str(f), "--kind", "reel", "-n", "300", "--json"])
    assert json.loads(capsys.readouterr().out)["kind"] == "reel"
