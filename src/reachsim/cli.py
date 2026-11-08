import argparse
import json
import sys

from . import instagram, planner
from .simulate import simulate


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reachsim")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="score a script/caption and suggest better hooks")
    a.add_argument("file", help="text file with your script, or - for stdin")
    a.add_argument("--niche", default="general")
    a.add_argument("--json", action="store_true")
    a.add_argument("--no-llm", action="store_true")
    p = sub.add_parser("plan", help="make a posting calendar")
    p.add_argument("--niche", default="general")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--per-day", type=int, default=1)
    g = sub.add_parser("post", help="publish a Reel to Instagram (dry-run unless --yes)")
    g.add_argument("video_url")
    g.add_argument("caption")
    g.add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "analyze":
        text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        r = simulate(text, args.niche, use_llm=False if args.no_llm else None)
        if args.json:
            print(json.dumps(r.__dict__, indent=2))
            return
        print(f"REACH SCORE: {r.score}/100 ({r.tier})  [{r.mode}]")
        print(f"hook {r.hook_score}  structure {r.structure_score}  ~{r.est_seconds}s")
        print(f"stop-scroll {r.stop_rate:.0%}  watch-through {r.avg_watch:.0%}  "
              f"share {r.share_rate:.1%}  follow {r.follow_rate:.1%}")
        for k, v in r.reactions.items():
            print(f"  {k}: {v}")
        print("\nFix these:" if r.issues else "")
        for i in r.issues:
            print(f"  - {i}")
        if r.hooks:
            print("\nTry these hooks:")
            for h in r.hooks:
                print(f"  * {h}")
    elif args.cmd == "plan":
        for s in planner.plan(args.niche, args.days, args.per_day):
            print(f"{s['date']} {s['time']}  {s['pillar']:<20} {s['idea']}")
    else:
        print(json.dumps(instagram.publish_reel(args.video_url, args.caption, args.yes), indent=2))


if __name__ == "__main__":
    main()
