import argparse
import json
import sys

from . import calibrate, instagram, planner, video
from .simulate import simulate


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reachsim")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="score a script/caption and suggest better hooks")
    a.add_argument("file", help="script .txt, - for stdin, or a video/audio file")
    a.add_argument("--niche", default="general")
    a.add_argument("--json", action="store_true")
    a.add_argument("--no-llm", action="store_true")
    a.add_argument("--save", metavar="NAME", help="remember this prediction for calibration")
    r = sub.add_parser("result", help="record real metrics: result NAME reach=1200 likes=80 ...")
    r.add_argument("name")
    r.add_argument("metrics", nargs="+")
    r.add_argument("--media-id", help="Instagram media id; fetch metrics automatically")
    sub.add_parser("calibrate", help="fit score weights from recorded real results")
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
        facts = None
        if args.file.lower().endswith(video.VIDEO_EXT):
            facts = video.transcribe(args.file)
            text = video.script(facts)
            print(f'Transcript: "{text[:200]}"
')
        else:
            text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        r = simulate(text, args.niche, use_llm=False if args.no_llm else None, facts=facts)
        if args.save:
            calibrate.record(args.save, r)
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
    elif args.cmd == "result":
        m = {}
        if args.media_id:
            for d in instagram.insights(args.media_id)["data"]:
                m[d["name"]] = d["values"][0]["value"]
        m.update({k: float(v) for k, v in (x.split("=") for x in args.metrics if "=" in x)})
        calibrate.update(args.name, **m)
        print(f"saved {args.name}: {m}")
    elif args.cmd == "calibrate":
        w, info = calibrate.fit()
        print(json.dumps({"weights": w, **info}, indent=2))
    elif args.cmd == "plan":
        for s in planner.plan(args.niche, args.days, args.per_day):
            print(f"{s['date']} {s['time']}  {s['pillar']:<20} {s['idea']}")
    else:
        print(json.dumps(instagram.publish_reel(args.video_url, args.caption, args.yes), indent=2))


if __name__ == "__main__":
    main()
