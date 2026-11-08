from reachsim import simulate
from reachsim.planner import plan

GOOD = ("Stop wasting 3 hours a day on this gym mistake. Most people never fix it. "
        "Do 3 sets, rest 60 seconds, and track every rep. Follow for more.")
BAD = ("Hey guys welcome back to my channel so today I am going to talk about something "
       "that I think is kind of interesting about the gym and how people work out in general "
       "and I hope you enjoy this video thanks for watching")


def test_good_beats_bad():
    g, b = simulate(GOOD, "fitness", use_llm=False), simulate(BAD, "fitness", use_llm=False)
    assert g.score > b.score
    assert g.hook_score > b.hook_score
    assert any("greeting" in i for i in b.issues)


def test_score_bounds():
    r = simulate("x", use_llm=False)
    assert 0 <= r.score <= 100


def test_plan_len():
    assert len(plan("fitness", 7, 2)) == 14


def test_calibration(tmp_path, monkeypatch):
    from reachsim import calibrate
    monkeypatch.setenv("REACHSIM_HOME", str(tmp_path))
    scripts = [BAD, GOOD, "Stop. 3 mistakes you make daily? Follow.", "hi everyone so today", GOOD + " Save this.", BAD + " more"]
    for i, s in enumerate(scripts):
        r = simulate(s, "fitness", use_llm=False)
        calibrate.record(f"p{i}", r)
        # fake reality: engagement tracks predicted score
        calibrate.update(f"p{i}", reach=1000, likes=r.score * 2, comments=0, shares=0, saved=0)
    w, info = calibrate.fit()
    assert info["score_corr"] > 0.9
    assert abs(sum(w.values()) - 1) < 0.01
    assert calibrate.weights() == w
