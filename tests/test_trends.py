import json

from thumbstop import trends

RSS = b"""<rss xmlns:ht="https://trends.google.com/trending/rss"><channel>
<item><title>creatine</title><ht:approx_traffic>200,000+</ht:approx_traffic></item>
<item><title>Some Football Game</title><ht:approx_traffic>1,000,000+</ht:approx_traffic></item></channel></rss>"""
REDDIT = b"""<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Why does my squat stall at 100kg?</title><link href="https://reddit.com/r/Fitness/x"/></entry>
<entry><title>Is creatine worth it?</title><link href="https://reddit.com/r/Fitness/y"/></entry></feed>"""


def test_parsers():
    g = trends.parse_google_rss(RSS)
    assert [(t.title, t.weight) for t in g] == [("creatine", 200000.0), ("Some Football Game", 1000000.0)]
    r = trends.parse_reddit(REDDIT, "Fitness")
    assert len(r) == 2 and r[0].source == "r/Fitness" and r[0].weight > r[1].weight and r[0].url.endswith("/x")
    assert trends.parse_hn({"hits": [{"title": "Show HN: x", "points": 50}]})[0].weight == 50


def test_ideas_ranked_and_deduped(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    found = trends.parse_google_rss(RSS) + trends.parse_reddit(REDDIT, "Fitness")
    out = trends.ideas(found, "fitness", n=5)
    assert len(out) == 4  # one idea per trend: creatine, football, 2 reddit questions
    assert out == sorted(out, key=lambda i: -i["hook_score"])
    assert len({i["hook"] for i in out}) == len(out)


def test_fetch_survives_network_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    def boom(*a, **k):
        raise OSError("offline")
    monkeypatch.setattr(trends, "_get", boom)
    monkeypatch.setattr(trends.time, "sleep", lambda s: None)
    found, errs = trends.fetch("fitness")
    assert found == [] and len(errs) >= 2


def test_recurring_mod_posts_are_not_ideas(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    found = [trends.Trend("Daily Simple Questions Thread - November 05, 2026", "r/Fitness"),
             trends.Trend("Is creatine worth it?", "r/Fitness")]
    assert [i["hook"] for i in trends.ideas(found, "fitness")] == ["Is creatine worth it?"]
