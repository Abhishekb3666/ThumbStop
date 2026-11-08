# ReachSim roadmap

**Goal:** a creator pastes a script/caption (later: a video) and gets a predicted reach score, the weak spots, and stronger hooks, before posting. Inspired by MiroFish's idea of simulating a crowd, but scoped to short-form content.

## Phases
| # | Phase | Status |
|---|-------|--------|
| 0 | Heuristic hook/structure scorer, 5 audience personas, CLI, calendar, IG publish stub | done |
| 1 | LLM persona simulation (Claude), rewritten hooks, `--json` output | done (needs `ANTHROPIC_API_KEY`) |
| 2 | **Calibration loop:** store predicted score vs real IG insights (`reachsim.instagram.insights`), fit weights so the score tracks reality | done (`analyze --save`, `result`, `calibrate`) |
| 3 | Video input: transcribe (Whisper), detect first-3s visuals/captions, pacing from cuts | |
| 4 | Niche-specific persona packs (fitness, finance, food, tech...) in YAML, community-contributed | |
| 5 | Web UI (Next.js on Vercel): paste script, see per-persona reactions | |
| 6 | Trend ingestion: pull trending audio/topics to seed ideas | |

## Own Instagram page (the dogfooding channel)
Account name suggestion: `@reachsim` / `@hook.lab`. Content: daily "I scored viral hooks, here's why" Reels, before/after hook rewrites, weekly leaderboard.
- **You must do once (I can't create accounts):** create the IG account, switch to Creator/Business, link a Facebook Page, create a Meta app, generate a long-lived token. Put `IG_USER_ID` and `IG_TOKEN` in env.
- **Cadence:** 1 Reel/day, rotating pillars (`reachsim plan`): myth-bust, quick win, story/result, list, reaction, behind-the-scenes, Q&A.
- **Loop:** draft script -> `reachsim analyze` -> fix until score >= 70 -> render video -> `reachsim post URL "caption" --yes` -> after 48h pull `insights` -> feed Phase 2 calibration.
- **Automation:** a scheduled daily job drafts + scores the next script and queues it for your approval; publishing stays one confirmed step so nothing posts unreviewed.

## Honesty note
The offline score is a heuristic proxy, not a guarantee of reach. Phase 2 exists to make it earn its credibility with real data.
