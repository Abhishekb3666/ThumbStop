# ThumbStop

Will your Reel/Short/TikTok get reach? ThumbStop simulates a small audience of viewer personas reacting to your script, then gives you a **reach score (0-100)**, what to fix, and **better hooks**.

```bash
pip install -e .            # offline heuristic mode, zero dependencies
pip install -e ".[llm]"     # + LLM persona simulation (set ANTHROPIC_API_KEY)

thumbstop analyze script.txt --niche fitness
thumbstop plan --niche fitness --days 7
thumbstop post https://example.com/reel.mp4 "caption"        # dry-run
thumbstop post https://example.com/reel.mp4 "caption" --yes  # publish (needs IG_USER_ID, IG_TOKEN)
```

Example:
```
REACH SCORE: 49/100 (average)  [heuristic]
Fix these:
  - Hook never addresses the viewer ('you') directly.
  - Under 8s: too short to deliver value or earn a follow.
```

See [ROADMAP.md](ROADMAP.md) for the roadmap. Contributions welcome: persona packs, better heuristics, calibration data. MIT licensed.

## Calibration (learn from your real results)
```bash
thumbstop analyze s.txt --save day1                 # remember the prediction
thumbstop result day1 --media-id <IG_MEDIA_ID> x=0  # or: result day1 reach=900 likes=50 comments=4 shares=9 saved=12
thumbstop calibrate                                 # after 5+ posts, re-weights the score toward what actually predicts engagement
```

## Video input
```bash
pip install -e ".[video]"
thumbstop analyze reel.mp4 --niche fitness   # transcribes, scores the real first 3s, dead air and pacing
```

## Persona packs
Each niche has its own audience and hook trigger words. `thumbstop packs` lists them; `--niche fitness` picks one.
Make your own by dropping `~/.thumbstop/packs/<niche>.json` (see `src/thumbstop/packs/fitness.json` for the format) - PRs with new packs are welcome.

## Web UI
```bash
python dev_server.py        # local preview at http://localhost:8000
vercel                      # deploy: Vercel picks up public/ and api/analyze.py
```
The public web version runs the offline scorer only. Set `THUMBSTOP_WEB_LLM=1` plus `ANTHROPIC_API_KEY` on the server to enable LLM mode (this spends your API credits on every visitor request).

## Trends -> hook ideas
```bash
thumbstop trends --niche fitness --ideas 5
```
Pulls what's trending (Google Trends, your niche's subreddits via Reddit RSS, Hacker News for tech) and ranks hook ideas with the same scorer you use on your own scripts. Add `"subreddits": [...]` to a pack to choose the sources. Reddit rate-limits anonymous clients; if a source fails you get a warning and the rest still work. Trending audio isn't covered: Instagram has no public API for it.
