import argparse
import json
import sys

from . import calibrate, content as C, crowd, instagram, llm, personas, planner, trends, video
from .simulate import simulate


def print_crowd(r, alts=()):
    m, ci = r.metrics, r.ci
    p = lambda k: f"{m[k]:.1%}" + (f" +/-{ci[k]:.1%}" if k in ci else "")
    print(f"CROWD SCORE: {r.score}/100 ({r.tier})   {r.kind} on {r.platform}, {r.n} simulated users, "
          f"{r.followers:.0%} followers, ~{r.duration}s")
    print(f"topics: {', '.join(r.topics) or 'none detected'}   (50 = a neutral average post, 100 = double on every metric)\n")
    print(f"skip rate {p('skip_rate')}   3s hold {p('hold_rate')}   avg watched {p('avg_watch_pct')}   "
          f"completion {p('completion_rate')}   replays {m['replay_rate']:.1%}")
    print(f"likes {p('like_rate')}   comments {p('comment_rate')}   shares {p('share_rate')}   saves {p('save_rate')}")
    print(f"profile visits {p('profile_visit_rate')}   follows {p('follow_rate')}   link clicks {m['link_click_rate']:.1%}   "
          f"engagement {m['engagement_rate']:.1%}   not interested {m['not_interested_rate']:.1%}")
    if r.slide_reach:
        print("\nReach per slide: " + "  ".join(f"{s['slide']}:{s['pct']:.0%}" for s in r.slide_reach))
    else:
        print("\nRetention: " + "  ".join(f"{x['at']}:{x['pct']:.0%}" for x in r.retention))
    for name, rows in r.segments.items():
        if name == "interest":
            continue
        print(f"\nBy {name.replace('_', ' ')}:")
        for label, v in rows.items():
            print(f"  {label:<11} n={v['n']:<5} skip {v['skip_rate']:.0%}  watched {v['avg_watch_pct']:.0%}  "
                  f"like {v['like_rate']:.1%}  share {v['share_rate']:.1%}  save {v['save_rate']:.1%}")
    for title, items in (("Insights", r.insights), ("Hook issues", r.hook_issues), ("Warnings", r.warnings)):
        if items:
            print(f"\n{title}:")
            for i in items:
                print(f"  - {i}")
    if alts:
        print("\nHook ranking (same crowd, same draws):")
        for a in alts:
            print(f"  [{a['score']:>3}] skip {a['skip_rate']:.0%}  {'(current) ' if a['current'] else ''}{a['hook']}")


def main(argv=None):
    try:
        _main(argv)
    except (FileNotFoundError, ValueError, KeyError) as e:  # user mistakes: one clean line, not a traceback
        sys.exit(f"thumbstop: error: {e.args[0] if isinstance(e, KeyError) else e}")


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="thumbstop")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="score a script/caption and suggest better hooks")
    a.add_argument("file", help="script .txt, - for stdin, or a video/audio file")
    a.add_argument("--niche", default="general")
    a.add_argument("--json", action="store_true")
    a.add_argument("--no-llm", action="store_true")
    a.add_argument("--save", metavar="NAME", help="remember this prediction for calibration")
    r = sub.add_parser("result", help="record real metrics: result NAME reach=1200 likes=80 ...")
    r.add_argument("name")
    r.add_argument("metrics", nargs="*")
    r.add_argument("--media-id", help="Instagram media id; fetch metrics automatically")
    sub.add_parser("calibrate", help="fit score weights from recorded real results")
    c = sub.add_parser("crowd", help="simulate a whole crowd (ages, user types, interests) on any post format")
    c.add_argument("input", help="script/post .txt, .json spec, video/audio file, image, folder of slides, or - for stdin")
    c.add_argument("--kind", help="reel, video, carousel, image, audio or text (inferred when omitted)")
    c.add_argument("--platform", default="instagram", help="instagram, tiktok, youtube, linkedin, x")
    c.add_argument("--niche", default="general")
    c.add_argument("--topics", default="", help="comma-separated interests, e.g. fitness,health")
    c.add_argument("--caption", default="")
    c.add_argument("-n", "--audience", type=int, default=2000, help="simulated viewers")
    c.add_argument("--followers", type=float, default=0.25, help="share of the crowd that already follows you")
    c.add_argument("--seed", type=int, default=7)
    c.add_argument("--hooks", action="store_true", help="LLM writes alternative hooks, the crowd re-scores each")
    c.add_argument("--json", action="store_true")
    c.add_argument("--save", metavar="NAME", help="remember this prediction for calibration")
    sub.add_parser("packs", help="list niche persona packs")
    t = sub.add_parser("trends", help="what is trending in your niche + hook ideas")
    t.add_argument("--niche", default="general")
    t.add_argument("--geo", default="US")
    t.add_argument("--ideas", type=int, default=5)
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
            print(f'Transcript: "{text[:200]}"\n')
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
    elif args.cmd == "trends":
        found, errs = trends.fetch(args.niche, args.geo)
        for i in trends.ideas(found, args.niche, args.ideas):
            print(f"[{i['hook_score']:>3}] {i['hook']}   ({i['source']})")
        if not found:
            print("No trends found.")
        for e in errs:
            print("warning:", e)
    elif args.cmd == "crowd":
        content = C.load(args.input, args.kind, args.caption, args.topics, args.niche)
        kw = dict(platform=args.platform, n=args.audience, followers=args.followers, seed=args.seed, niche=args.niche)
        r = crowd.run(content, **kw)
        if args.save:
            calibrate.record(args.save, r)
        alts = []
        if args.hooks:
            ideas = llm.hooks(content.text, args.niche, content.kind) if llm.available() else []
            if ideas:
                alts = crowd.rank_hooks(content, ideas, **kw)
            else:
                print("note: --hooks needs `pip install thumbstop[llm]` and ANTHROPIC_API_KEY (or the call failed)", file=sys.stderr)
        if args.json:
            print(json.dumps({**r.__dict__, "hook_ranking": alts}, indent=2))
        else:
            print_crowd(r, alts)
    elif args.cmd == "packs":
        print("\n".join(personas.available()))
        print("add your own:", calibrate.home() / "packs" / "<niche>.json")
    elif args.cmd == "plan":
        for s in planner.plan(args.niche, args.days, args.per_day):
            print(f"{s['date']} {s['time']}  {s['pillar']:<20} {s['idea']}")
    else:
        print(json.dumps(instagram.publish_reel(args.video_url, args.caption, args.yes), indent=2))


if __name__ == "__main__":
    main()
