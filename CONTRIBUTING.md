# Contributing to ThumbStop

Thanks for helping! Good places to start: issues labelled [`good first issue`](https://github.com/Abhishekb3666/thumbstop/labels/good%20first%20issue) and [`help wanted`](https://github.com/Abhishekb3666/thumbstop/labels/help%20wanted).

## Setup
```bash
git clone https://github.com/Abhishekb3666/thumbstop && cd thumbstop
pip install -e ".[dev]"
python -m pytest -q                 # ~15s, must pass
python scripts/validate.py          # model sanity report, must end with ALL CHECKS PASSED
python dev_server.py                # web UI at http://localhost:8000
```
Zero runtime dependencies is a goal: optional features (`[llm]`, `[video]`) stay optional, and anything that needs the network must fail gracefully.

## Where things live
| Area | Files |
|------|-------|
| Crowd model and metrics | `src/thumbstop/crowd.py`, `demographics.py` |
| Content formats, features, loaders | `src/thumbstop/content.py` |
| Hook/pacing heuristics | `src/thumbstop/heuristics.py` |
| Niche persona packs (JSON) | `src/thumbstop/packs/` |
| Video/audio | `src/thumbstop/video.py` |
| Trends | `src/thumbstop/trends.py` |
| Instagram publishing | `src/thumbstop/instagram.py` |
| Web (Vercel) | `api/`, `public/index.html` |

## Pull requests
- Keep them focused, and add a test for new behavior.
- **Changes to the model** (anything in `crowd.py`, `demographics.py`, `heuristics.py`) must keep `scripts/validate.py` passing; say in the PR what moved and why, and cite a source when you change a population number.
- Never commit tokens or `.env` files. Real-account tests belong behind environment variables, not in the suite.
- Be kind in reviews. This is a small friendly project.

## Reporting results
The most valuable contribution is **real data**: predicted score vs actual reach/engagement for your own posts (`thumbstop analyze --save` / `thumbstop result`). Open an issue with anonymized numbers.
