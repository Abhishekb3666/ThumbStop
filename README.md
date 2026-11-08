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
