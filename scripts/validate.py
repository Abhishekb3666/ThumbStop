"""Model validation report: python scripts/validate.py
Checks that the simulation behaves sensibly (stability, direction of effects, ordering vs a human-labelled
ladder, segment face-validity, score distribution, calibration recovery, speed).
It can NOT prove predictive accuracy: that needs your real post results (see `thumbstop calibrate`)."""
import os
import random
import statistics as st
import sys
import tempfile
import time

os.environ.setdefault("THUMBSTOP_HOME", tempfile.mkdtemp())
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thumbstop import calibrate, content as C, crowd  # noqa: E402

SEEDS = range(1, 21)
N = 1500


def score(c, seed=7, n=N, **kw):
    kw.setdefault("niche", "fitness")
    return crowd.run(c, seed=seed, n=n, **kw)


def reel(text, **kw):
    return C.from_text("reel", text, niche="fitness", **kw)


def mean_over_seeds(c, key=lambda r: r.score, **kw):
    return st.mean(key(score(c, s, **kw)) for s in SEEDS)


def spearman(a, b):
    return calibrate.spearman(a, b)


# human-labelled quality ladder (1 = poor ... 5 = strong), written from common short-form guidance
LADDER = [
    (1, "Hey guys welcome back to my channel, so today I want to talk about some stuff about the gym that I think is kind of interesting, and I hope you all enjoy it, thanks for watching."),
    (1, "Um so yeah today we are going to talk about working out in general and stuff like that okay."),
    (2, "Today I'm sharing my gym routine. I go to the gym five days a week and do different exercises each day."),
    (2, "Here are some thoughts on fitness and why it matters for your health in the long run."),
    (3, "How to build muscle faster. Eat enough protein, sleep well, and train progressively. Follow for more tips."),
    (3, "Three tips for a better workout. Warm up, track your lifts, and rest between sets."),
    (4, "Stop doing this at the gym. Most people skip warm-ups and get injured. Do 5 minutes of mobility first. Save this."),
    (4, "Why you're not gaining muscle: you eat 30g less protein than you think. Track it for 3 days. Send this to your gym buddy."),
    (5, "You're wasting 3 hours a week on this gym mistake. Nobody tells you the real reason your squat stalls. Fix your ankle mobility in 2 minutes: do this drill 3 times a day. Save this and send it to your lifting partner."),
    (5, "The truth about creatine nobody tells you: 5 grams a day beats loading. Here's the 3 step way to take it. Comment CREATINE and I'll send the guide."),
]

BASE = "Most people lift wrong. Here is how to fix your squat with simple cues and good form for better results over time."
ABLATIONS = [  # (name, text, expected sign of score change)
    ("greeting added", "Hey guys welcome back to my channel. " + BASE, -1),
    ("number + tension in hook", "3 cues fix your squat mistake nobody tells you. Here is how with simple form for better results over time.", +1),
    ("call to action added", BASE + " Save this for your next leg day.", +1),
    ("question added", BASE + " Which cue do you miss?", +1),
    ("far too long (x8)", " ".join([BASE] * 8), -1),
    ("far too short", "Fix your squat.", -1),
]


def section(t):
    print(f"\n=== {t} ===")


def main():
    fails = []

    def check(ok, msg):
        print(("  PASS  " if ok else "  FAIL  ") + msg)
        if not ok:
            fails.append(msg)

    section("1. Stability: same post, 20 different crowds (n=%d)" % N)
    for name, txt in (("weak", LADDER[1][1]), ("mid", LADDER[4][1]), ("strong", LADDER[8][1])):
        sc = [score(reel(txt), s).score for s in SEEDS]
        print(f"  {name:6} score mean {st.mean(sc):5.1f}  sd {st.pstdev(sc):4.1f}  range {min(sc)}-{max(sc)}")
        check(st.pstdev(sc) < 5, f"{name}: score sd {st.pstdev(sc):.1f} < 5")
    wins = sum(score(reel(LADDER[8][1]), s).score > score(reel(LADDER[1][1]), s).score for s in SEEDS)
    check(wins == len(SEEDS), f"strong beats weak in {wins}/{len(SEEDS)} crowds")

    section("2. Direction of effects (mean over 20 seeds, vs base post)")
    b = mean_over_seeds(reel(BASE))
    print(f"  base score {b:.1f}")
    for name, txt, sign in ABLATIONS:
        d = mean_over_seeds(reel(txt)) - b
        print(f"  {name:28} {d:+6.1f}")
        check(d * sign > 0, f"'{name}' moves score the expected way ({d:+.1f})")

    section("3. Ordering vs human-labelled ladder (10 reels)")
    labels = [l for l, _ in LADDER]
    scores = [mean_over_seeds(reel(t)) for _, t in LADDER]
    rho = spearman(labels, scores)
    pairs = [(i, j) for i in range(len(LADDER)) for j in range(len(LADDER)) if labels[i] > labels[j]]
    acc = sum(scores[i] > scores[j] for i, j in pairs) / len(pairs)
    for (l, t), s in zip(LADDER, scores):
        print(f"  label {l}  score {s:5.1f}  {t[:60]}")
    check(rho >= 0.8, f"Spearman vs labels {rho:.2f} >= 0.8")
    check(acc >= 0.9, f"pairwise ordering accuracy {acc:.0%} >= 90%")

    section("4. Segment face validity")
    gaming = reel("New game just dropped and the level design is insane. The boss fight is the best I have played all year. Follow for more.")
    gaming.topics = ["gaming"]
    r = score(gaming, platform="tiktok", n=4000).segments["age"]
    check(r["13-17"]["skip_rate"] < r["55+"]["skip_rate"], f"gaming: teens skip {r['13-17']['skip_rate']:.0%} < 55+ skip {r['55+']['skip_rate']:.0%}")
    news = reel("Breaking: the government just changed tax policy and here is what it means for the economy. Follow for more.")
    news.topics = ["news"]
    r = score(news, platform="instagram", n=4000).segments["age"]
    check(r["55+"]["skip_rate"] < r["18-24"]["skip_rate"], f"news: 55+ skip {r['55+']['skip_rate']:.0%} < 18-24 skip {r['18-24']['skip_rate']:.0%}")
    seg = score(reel(LADDER[8][1]), followers=0.4, n=4000).segments["audience"]
    check(seg["followers"]["skip_rate"] < seg["cold feed"]["skip_rate"], "followers skip less than cold feed")
    txt = C.from_text("text", "Hot take: most gyms are a scam. 20 minutes of bodyweight work beats a membership you never use. What do you think?", niche="fitness")
    check(score(txt, platform="x").metrics["skip_rate"] < score(txt, platform="tiktok").metrics["skip_rate"], "text skips less on X than TikTok")
    check(score(reel(LADDER[8][1]), platform="tiktok").metrics["skip_rate"] < score(C.from_text("image", "Gym mistakes", niche="fitness"), platform="tiktok").metrics["skip_rate"],
          "TikTok favors reels over images")

    section("5. Topic neutrality: same execution, different topic")
    tmpl = "Stop wasting 3 hours a week on this {w} mistake. Nobody tells you the real reason. Do this 3 step fix. Save this."
    sc = {}
    for w, t in (("gym", "fitness"), ("budget", "finance"), ("recipe", "food"), ("game", "gaming"), ("election", "news")):
        c = C.from_text("reel", tmpl.format(w=w), niche="general")
        c.topics = [t]
        sc[t] = mean_over_seeds(c, niche="general")
    print("  " + "  ".join(f"{k} {v:.0f}" for k, v in sc.items()))
    check(max(sc.values()) - min(sc.values()) < 10, f"score spread across topics {max(sc.values()) - min(sc.values()):.1f} < 10")

    section("6. Score distribution on a mixed corpus (all formats)")
    corpus = [reel(t) for _, t in LADDER]
    corpus += [C.from_text("carousel", "", slides=s, niche="fitness") for s in (
        ["Gym stuff", "Some things about working out", "Thanks for reading"],
        ["5 gym mistakes killing your gains", "1. No warm-up", "2. Ego lifting", "3. No tracking", "Save this"],
        ["My routine", "Monday chest", "Tuesday back", "Wednesday rest", "Thursday legs", "Friday arms", "Saturday rest", "Sunday rest", "Follow me"])]
    corpus += [C.from_text("text", t, niche="fitness") for t in (
        "Went to the gym today.", "Hot take: you don't need a gym. 20 minutes of bodyweight work 3x a week beats a membership. What do you think?",
        "Thoughts on training. It is important to train regularly and eat well and sleep and also manage stress and take care of mobility over time.")]
    allsc = [mean_over_seeds(c) for c in corpus]
    med = st.median(allsc)
    print(f"  n={len(allsc)} median {med:.0f}  min {min(allsc):.0f}  max {max(allsc):.0f}  >=75: {sum(s >= 75 for s in allsc)}  <35: {sum(s < 35 for s in allsc)}")
    check(40 <= med <= 65, f"median score {med:.0f} within 40-65 (50 should mean average)")
    check(sum(s >= 75 for s in allsc) <= len(allsc) * 0.25, "'viral potential' (>=75) is rare (<=25% of corpus)")

    section("7. Calibration recovers a planted truth")
    rng = random.Random(3)
    home = tempfile.mkdtemp()
    os.environ["THUMBSTOP_HOME"] = home
    for i in range(30):
        c = reel(rng.choice(LADDER)[1] + " " + rng.choice(["", "Save this.", "Which one are you?"]))
        r = score(c, seed=100 + i, n=600)
        calibrate.record(f"p{i}", r)
        truth = (0.2 + 6 * r.metrics["share_rate"]) * rng.uniform(0.85, 1.15)  # reality driven by shares
        calibrate.update(f"p{i}", reach=1000, likes=0, comments=0, shares=truth * 1000, saved=0)
    w, info = calibrate.fit()
    print(f"  weights {w}  score_corr {info['score_corr']}")
    check(info["score_corr"] > 0.3, f"predicted score correlates with planted truth ({info['score_corr']})")
    cc = info["component_corr"]
    check(cc["share"] == max(cc.values()), f"share has the highest correlation with the planted truth {cc}")
    check(w["share"] > 0.2 + 0.05, f"share weight rose above its 0.20 default ({w['share']})")

    section("8. Speed")
    for n in (2000, 10000, 50000):
        t = time.time()
        score(reel(LADDER[8][1]), n=n)
        print(f"  n={n:<6} {time.time() - t:5.2f}s")
    t = time.time()
    score(reel(LADDER[8][1]), n=10000)
    check(time.time() - t < 5, "10,000 users simulate in < 5s")

    print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
