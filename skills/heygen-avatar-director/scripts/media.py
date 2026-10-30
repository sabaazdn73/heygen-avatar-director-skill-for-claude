#!/usr/bin/env python3
"""Review and join tools for avatar clips. Needs ffmpeg and ffprobe on the PATH.

  media.py sheet clip.mp4 [--every 0.5] [--cols 6] [--out clip.sheet.jpg]   contact sheet with timestamps
  media.py frames clip.mp4 [--every 0.5] [--out frames/]                    single frames as JPEGs
  media.py motion clip.mp4 [--fps 10]                                       movement score per second
  media.py join final.mp4 a.mp4 b.mp4 ...                                   join beats into one video
"""
import argparse
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def need_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} is not installed or not on the PATH")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        die(f"{cmd[0]} failed: {r.stderr.decode(errors='replace')[-800:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=width,height:format=duration", "-of", "default=nw=1", path]).decode()
    info = dict(line.split("=", 1) for line in out.split() if "=" in line)
    return float(info.get("duration", 0)), int(info.get("width", 0)), int(info.get("height", 0))


def cmd_sheet(a):
    need_ffmpeg()
    dur, _, _ = probe(a.clip)
    n = max(1, round(dur / a.every))
    rows = math.ceil(n / a.cols)
    out = a.out or os.path.splitext(a.clip)[0] + ".sheet.jpg"
    vf = (f"fps=1/{a.every},scale=360:-2,"
          "drawtext=text='%{pts\\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,"
          f"tile={a.cols}x{rows}:padding=4:margin=4")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.clip, "-vf", vf, "-frames:v", "1", out],
                       capture_output=True)
    if r.returncode != 0:  # drawtext needs a font; fall back to a sheet without timestamps
        vf = f"fps=1/{a.every},scale=360:-2,tile={a.cols}x{rows}:padding=4:margin=4"
        run(["ffmpeg", "-y", "-v", "error", "-i", a.clip, "-vf", vf, "-frames:v", "1", out])
        print("note: timestamps skipped (ffmpeg drawtext unavailable); frames run left to right, "
              f"one every {a.every}s", file=sys.stderr)
    print(f"{out}\t{n} frames, one every {a.every}s, {dur:.1f}s clip")


def cmd_frames(a):
    need_ffmpeg()
    os.makedirs(a.out, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", a.clip, "-vf", f"fps=1/{a.every},scale=720:-2",
         os.path.join(a.out, "f_%04d.jpg")])
    files = sorted(f for f in os.listdir(a.out) if f.startswith("f_"))
    for i, f in enumerate(files):
        print(f"{os.path.join(a.out, f)}\t{i * a.every:.1f}s")


def cmd_motion(a):
    """Mean absolute pixel change between consecutive small grey frames, per second.

    Seconds far below the clip's own median look frozen; far above look jittery or like a jump cut.
    It measures movement, not quality: use it to decide where to look, then look.
    """
    need_ffmpeg()
    dur, _, _ = probe(a.clip)
    w, h = 64, 36
    raw = run(["ffmpeg", "-v", "error", "-i", a.clip, "-vf", f"fps={a.fps},scale={w}:{h},format=gray",
               "-f", "rawvideo", "-"])
    size = w * h
    frames = [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]
    if len(frames) < 2:
        die("clip too short to measure")
    diffs = [sum(abs(x - y) for x, y in zip(f1, f2)) / size for f1, f2 in zip(frames, frames[1:])]
    per_sec = []
    for s in range(math.ceil(len(diffs) / a.fps)):
        chunk = diffs[s * a.fps:(s + 1) * a.fps]
        if chunk:
            per_sec.append(sum(chunk) / len(chunk))
    med = statistics.median(per_sec) or 1e-9
    print(f"clip {a.clip}: {dur:.1f}s, median movement {med:.2f}")
    print("second\tmovement\tvs median\tflag")
    for s, v in enumerate(per_sec):
        ratio = v / med
        flag = "frozen?" if ratio < 0.35 else ("jittery or jump?" if ratio > 2.5 else "")
        print(f"{s}-{s + 1}s\t{v:.2f}\t{ratio:.2f}x\t{flag}")


def cmd_join(a):
    need_ffmpeg()
    if len(a.clips) < 2:
        die("give at least two clips")
    dims = {probe(c)[1:] for c in a.clips}
    if len(dims) > 1:
        print(f"warning: clips have different sizes {sorted(dims)}; framing will jump. "
              "Render every beat with the same aspect_ratio, fit and resolution.", file=sys.stderr)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for c in a.clips:
            lst.write(f"file '{os.path.abspath(c)}'\n")
    try:
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst.name,
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", a.out])
    finally:
        os.unlink(lst.name)
    print(f"{a.out}\t{probe(a.out)[0]:.1f}s from {len(a.clips)} clips")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("clip")
    s.add_argument("--every", type=float, default=0.5)
    s.add_argument("--cols", type=int, default=6)
    s.add_argument("--out")
    s.set_defaults(fn=cmd_sheet)
    s = sub.add_parser("frames")
    s.add_argument("clip")
    s.add_argument("--every", type=float, default=0.5)
    s.add_argument("--out", default="frames")
    s.set_defaults(fn=cmd_frames)
    s = sub.add_parser("motion")
    s.add_argument("clip")
    s.add_argument("--fps", type=int, default=10)
    s.set_defaults(fn=cmd_motion)
    s = sub.add_parser("join")
    s.add_argument("out")
    s.add_argument("clips", nargs="+")
    s.set_defaults(fn=cmd_join)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
