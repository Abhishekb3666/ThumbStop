"""Instagram Graph API publishing (Reels) + insights. Requires an Instagram Business/Creator
account linked to a Facebook Page. Env: IG_USER_ID, IG_TOKEN. The video must be at a public URL.
Dry-run unless confirm=True so nothing posts by accident."""
import json
import os
import time
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"


def _call(path, params, method="POST"):
    params = {**params, "access_token": os.environ["IG_TOKEN"]}
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{API}/{path}" + (f"?{q}" if method == "GET" else ""),
                                 data=None if method == "GET" else q.encode(), method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def publish_reel(video_url: str, caption: str, confirm: bool = False):
    if not confirm:
        return {"dry_run": True, "video_url": video_url, "caption": caption}
    uid = os.environ["IG_USER_ID"]
    cid = _call(f"{uid}/media", {"media_type": "REELS", "video_url": video_url, "caption": caption})["id"]
    for _ in range(30):  # wait for Instagram to finish processing the video
        st = _call(cid, {"fields": "status_code"}, "GET")["status_code"]
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise RuntimeError("Instagram failed to process the video")
        time.sleep(10)
    return _call(f"{uid}/media_publish", {"creation_id": cid})


def insights(media_id: str):
    """Real performance, to compare against reachsim's predicted score."""
    return _call(f"{media_id}/insights", {"metric": "reach,likes,comments,shares,saved,plays"}, "GET")
