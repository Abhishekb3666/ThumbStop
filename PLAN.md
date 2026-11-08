# ThumbStop roadmap

**Goal:** a creator pastes a script/caption (later: a video) and gets a predicted reach score, the weak spots, and stronger hooks, before posting. Inspired by MiroFish's idea of simulating a crowd, but scoped to short-form content.

## Phases
| # | Phase | Status |
|---|-------|--------|
| 0 | Heuristic hook/structure scorer, 5 audience personas, CLI, calendar, IG publish stub | done |
| 1 | LLM persona simulation (Claude), rewritten hooks, `--json` output | done (needs `ANTHROPIC_API_KEY`) |
| 2 | **Calibration loop:** store predicted score vs real IG insights (`thumbstop.instagram.insights`), fit weights so the score tracks reality | done (`analyze --save`, `result`, `calibrate`) |
| 3 | Video input: Whisper transcript, real first-3s hook, duration, dead air, pace (scene-cut and visual checks still todo) | done |
| 4 | Niche persona packs: JSON files (built-in fitness, finance, food, tech; yours in ~/.thumbstop/packs) with niche hook words | done |
| 5 | Web UI: static page + Python function on Vercel (`public/`, `api/analyze.py`), local preview via `python dev_server.py` | done |
| 6 | Trend ingestion: pull trending audio/topics to seed ideas | |

## Own Instagram page (the dogfooding channel)
Account name suggestion: ``@thumbstop` or `@thumbstop.ai`. Content: daily "I scored viral hooks, here's why" Reels, before/after hook rewrites, weekly leaderboard.
- **You must do once (I can't create accounts):** create the IG account, switch to Creator/Business, link a Facebook Page, create a Meta app, generate a long-lived token. Put `IG_USER_ID` and `IG_TOKEN` in env.
- **Cadence:** 1 Reel/day, rotating pillars (`thumbstop plan`): myth-bust, quick win, story/result, list, reaction, behind-the-scenes, Q&A.
- **Loop:** draft script -> `thumbstop analyze` -> fix until score >= 70 -> render video -> `thumbstop post URL "caption" --yes` -> after 48h pull `insights` -> feed Phase 2 calibration.
- **Automation:** a scheduled daily job drafts + scores the next script and queues it for your approval; publishing stays one confirmed step so nothing posts unreviewed.

## Honesty note
The offline score is a heuristic proxy, not a guarantee of reach. Phase 2 exists to make it earn its credibility with real data.
