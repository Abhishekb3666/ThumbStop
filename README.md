# ReachSim

Will your Reel/Short/TikTok get reach? ReachSim simulates a small audience of viewer personas reacting to your script, then gives you a **reach score (0-100)**, what to fix, and **better hooks**.

```bash
pip install -e .            # offline heuristic mode, zero dependencies
pip install -e ".[llm]"     # + Claude-powered persona simulation (set ANTHROPIC_API_KEY)

reachsim analyze script.txt --niche fitness
reachsim plan --niche fitness --days 7
reachsim post https://example.com/reel.mp4 "caption"        # dry-run
reachsim post https://example.com/reel.mp4 "caption" --yes  # publish (needs IG_USER_ID, IG_TOKEN)
```

Example:
```
REACH SCORE: 49/100 (average)  [heuristic]
Fix these:
  - Hook never addresses the viewer ('you') directly.
  - Under 8s: too short to deliver value or earn a follow.
```

See [PLAN.md](PLAN.md) for the roadmap. Contributions welcome: persona packs, better heuristics, calibration data. MIT licensed.

## Calibration (learn from your real results)
```bash
reachsim analyze s.txt --save day1                 # remember the prediction
reachsim result day1 --media-id <IG_MEDIA_ID> x=0  # or: result day1 reach=900 likes=50 comments=4 shares=9 saved=12
reachsim calibrate                                 # after 5+ posts, re-weights the score toward what actually predicts engagement
```
