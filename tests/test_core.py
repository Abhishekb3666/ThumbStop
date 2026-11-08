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
