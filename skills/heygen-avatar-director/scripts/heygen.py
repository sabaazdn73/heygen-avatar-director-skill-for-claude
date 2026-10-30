#!/usr/bin/env python3
"""Small client for the HeyGen v3 API, used by the HeyGen Avatar Director skill.

Standard library only. Reads the API key from the HEYGEN_API_KEY environment variable
and never prints it.

  heygen.py whoami
  heygen.py looks [--type digital_twin|photo_avatar|studio_avatar] [--private|--public] [--limit N]
  heygen.py voices [--language English] [--gender female|male] [--private] [--limit N]
  heygen.py render plan.json [--beat ID ...] [--dry-run]
  heygen.py wait --state plan.state.json --out renders/   (or: wait VIDEO_ID --out clip.mp4)
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.heygen.com"
ENGINES = {"avatar_v", "avatar_iv", "avatar_iii"}
VIDEO_AVATAR_TYPES = {"digital_twin", "studio_avatar"}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def api_key():
    key = os.environ.get("HEYGEN_API_KEY", "").strip()
    if not key:
        die("HEYGEN_API_KEY is not set. Create a key in HeyGen (Settings > API) and export it in your own shell.")
    return key


def request(method, path, params=None, body=None, idempotency_key=None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    headers = {"x-api-key": api_key(), "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            if e.code == 429 and attempt < 3:
                wait = int(e.headers.get("Retry-After") or 10)
                print(f"rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            try:
                err = json.loads(raw).get("error", {})
                die(f"HTTP {e.code} {err.get('code', '')}: {err.get('message', raw)}"
                    + (f" (param: {err['param']})" if err.get("param") else "")
                    + (f" see {err['doc_url']}" if err.get("doc_url") else ""))
            except (ValueError, AttributeError):
                die(f"HTTP {e.code}: {raw[:500]}")
        except urllib.error.URLError as e:
            die(f"could not reach {BASE}: {e.reason}")
    die("gave up after repeated rate limiting")


def paged(path, params, limit):
    out, token = [], None
    while len(out) < limit:
        p = dict(params, limit=min(50, limit - len(out)), token=token)
        res = request("GET", path, p)
        out += res.get("data", [])
        token = res.get("next_token")
        if not res.get("has_more") or not token:
            break
    return out[:limit]


# ---------- listing ----------

def cmd_whoami(a):
    res = request("GET", "/v3/users/me")
    print(json.dumps(res.get("data", res), indent=2))


def cmd_looks(a):
    params = {"avatar_type": a.type}
    if a.private:
        params["ownership"] = "private"
    elif a.public:
        params["ownership"] = "public"
    looks = paged("/v3/avatars/looks", params, a.limit)
    for l in looks:
        engines = ",".join(l.get("supported_api_engines") or []) or "?"
        extra = f" status={l['status']}" if l.get("status") else ""
        print(f"{l['id']}\t{l.get('avatar_type', '?')}\t{engines}\tvoice={l.get('default_voice_id') or '-'}\t{l.get('name', '')}{extra}")
    print(f"{len(looks)} looks", file=sys.stderr)


def cmd_voices(a):
    params = {"type": "private" if a.private else "public", "language": a.language, "gender": a.gender}
    voices = paged("/v3/voices", params, a.limit)
    for v in voices:
        print(f"{v['voice_id']}\t{v.get('language', '')}\t{v.get('gender', '')}\tpause={v.get('support_pause')}\t{v.get('name', '')}")
    print(f"{len(voices)} voices", file=sys.stderr)


# ---------- render ----------

def build_body(plan, beat):
    """Turn one beat of a direction plan into a POST /v3/videos body, plus warnings."""
    warnings = []
    engine = beat.get("engine", plan.get("engine", "avatar_iv"))
    if engine not in ENGINES:
        die(f"beat {beat['id']}: unknown engine '{engine}' (use one of {sorted(ENGINES)})")
    avatar_type = plan.get("avatar_type")
    body = {
        "type": "avatar",
        "avatar_id": beat.get("avatar_id", plan["avatar_id"]),
        "script": beat["script"],
        "voice_id": beat.get("voice_id", plan.get("voice_id")),
        "resolution": plan.get("resolution", "1080p"),
        "aspect_ratio": plan.get("aspect_ratio", "16:9"),
        "caption": {"file_format": "srt"},
        "title": f"{plan.get('title', 'avatar video')} - {beat['id']}",
    }
    if not body["voice_id"]:
        del body["voice_id"]
        warnings.append("no voice_id: HeyGen will use the avatar's default voice if it has one")
    for key in ("fit", "background", "remove_background"):
        if key in plan:
            body[key] = plan[key]

    vs = dict(plan.get("voice_settings", {}))
    if "speed" in beat:
        vs["speed"] = beat["speed"]
    if "pitch" in beat:
        vs["pitch"] = beat["pitch"]
    if vs:
        if not 0.5 <= vs.get("speed", 1) <= 1.5:
            die(f"beat {beat['id']}: speed must be between 0.5 and 1.5")
        if not -50 <= vs.get("pitch", 0) <= 50:
            die(f"beat {beat['id']}: pitch must be between -50 and 50")
        body["voice_settings"] = vs

    eng = {"type": engine}
    if engine == "avatar_v":
        if plan.get("more_blinking") or beat.get("more_blinking"):
            eng["more_blinking"] = True
        if plan.get("reference_look_id"):
            eng["reference_look_id"] = plan["reference_look_id"]
    body["engine"] = eng

    motion = beat.get("motion_prompt")
    if motion:
        if engine == "avatar_iv" and avatar_type in VIDEO_AVATAR_TYPES:
            warnings.append("motion_prompt dropped: Avatar IV rejects it for video avatars (try engine avatar_v)")
        else:
            body["motion_prompt"] = motion
    expr = beat.get("expressiveness")
    if expr:
        if expr not in ("low", "medium", "high"):
            die(f"beat {beat['id']}: expressiveness must be low, medium or high")
        if engine == "avatar_v":
            warnings.append("expressiveness dropped: not available on Avatar V")
        elif avatar_type and avatar_type != "photo_avatar":
            warnings.append("expressiveness dropped: only photo avatars support it")
        else:
            body["expressiveness"] = expr
    if not avatar_type:
        warnings.append("plan has no avatar_type, so engine checks were limited; HeyGen will reject unsupported settings")
    return body, warnings


def idem_key(body):
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:40]
    return f"avatar-director:{digest}"


def cmd_render(a):
    with open(a.plan) as f:
        plan = json.load(f)
    for k in ("avatar_id", "beats"):
        if k not in plan:
            die(f"plan is missing '{k}'")
    beats = [b for b in plan["beats"] if not a.beat or b["id"] in a.beat]
    if not beats:
        die("no beats selected")
    state_path = os.path.splitext(a.plan)[0] + ".state.json"
    state = {}
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
    for beat in beats:
        body, warnings = build_body(plan, beat)
        for w in warnings:
            print(f"[{beat['id']}] warning: {w}", file=sys.stderr)
        if a.dry_run:
            print(f"--- {beat['id']} ---")
            print(json.dumps(body, indent=2))
            continue
        res = request("POST", "/v3/videos", body=body, idempotency_key=idem_key(body))
        vid = res.get("data", {}).get("video_id")
        if not vid:
            die(f"beat {beat['id']}: no video_id in response: {res}")
        state[beat["id"]] = {"video_id": vid, "submitted": int(time.time())}
        print(f"{beat['id']}\t{vid}\t{res['data'].get('status')}")
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
    if not a.dry_run:
        print(f"saved video ids to {state_path}", file=sys.stderr)


# ---------- wait / download ----------

def download(url, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(path, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def wait_one(video_id, out, timeout):
    start = time.time()
    while True:
        data = request("GET", f"/v3/videos/{video_id}").get("data", {})
        status = data.get("status")
        if status == "completed":
            break
        if status == "failed":
            print(f"{video_id} failed: {data.get('failure_code')}: {data.get('failure_message')}", file=sys.stderr)
            return False
        if time.time() - start > timeout:
            print(f"{video_id} still {status} after {timeout}s; run wait again later", file=sys.stderr)
            return False
        time.sleep(15)
    download(data["video_url"], out)
    # Save any caption file HeyGen returns next to the video.
    for k, v in data.items():
        if isinstance(v, str) and v.startswith("http") and ("caption" in k or "subtitle" in k):
            download(v, os.path.splitext(out)[0] + ".srt")
    print(f"{video_id}\tcompleted\t{data.get('duration')}s\t{out}")
    return True


def cmd_wait(a):
    if a.state:
        with open(a.state) as f:
            state = json.load(f)
        os.makedirs(a.out, exist_ok=True)
        ok = all([wait_one(v["video_id"], os.path.join(a.out, f"{bid}.mp4"), a.timeout) for bid, v in state.items()])
    elif a.video_id:
        out = a.out if a.out.endswith((".mp4", ".webm")) else os.path.join(a.out, f"{a.video_id}.mp4")
        ok = wait_one(a.video_id, out, a.timeout)
    else:
        die("give a VIDEO_ID or --state")
    sys.exit(0 if ok else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)
    s = sub.add_parser("looks")
    s.add_argument("--type", choices=["digital_twin", "photo_avatar", "studio_avatar"])
    g = s.add_mutually_exclusive_group()
    g.add_argument("--private", action="store_true")
    g.add_argument("--public", action="store_true")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_looks)
    s = sub.add_parser("voices")
    s.add_argument("--language")
    s.add_argument("--gender", choices=["male", "female"])
    s.add_argument("--private", action="store_true")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_voices)
    s = sub.add_parser("render")
    s.add_argument("plan")
    s.add_argument("--beat", nargs="*", help="render only these beat ids")
    s.add_argument("--dry-run", action="store_true", help="print request bodies and warnings, send nothing")
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser("wait")
    s.add_argument("video_id", nargs="?")
    s.add_argument("--state")
    s.add_argument("--out", default="renders")
    s.add_argument("--timeout", type=int, default=1800)
    s.set_defaults(fn=cmd_wait)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
