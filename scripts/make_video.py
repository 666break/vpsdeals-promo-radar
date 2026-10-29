#!/usr/bin/env python3
"""Build a 30-60s explainer video from article slides.

Pipeline: slide spec (JSON) -> HTML -> Chrome headless PNG -> edge-tts narration
-> per-slide segment -> concat -> burned-in captions -> final MP4 + SRT.

No generative video model is involved: every frame is a still rendered from
text that already exists on the article page, and the narration is synthetic
text-to-speech. Deterministic, re-runnable, no stock footage.

Usage: python scripts/make_video.py spec.json out_dir
"""
import json
import os
import subprocess
import sys
import asyncio
import shutil
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1920, 1080
VOICE = "en-US-AndrewNeural"

PALETTE = dict(bg="#eef1f6", surface="#ffffff", border="#e3e8ef", text="#16202c",
               muted="#5b6675", muted2="#8a94a3", primary="#2563eb", accent="#0ca678")


def html_for(slide, idx, total, brand):
    p = PALETTE
    stats = slide.get("stats") or []
    bullets = slide.get("bullets") or []
    stats_html = ""
    if stats:
        cells = "".join(
            f'<div class="stat"><div class="sv">{s["value"]}</div>'
            f'<div class="sl">{s["label"]}</div>'
            f'<div class="sn">{s.get("sub","")}</div></div>' for s in stats)
        stats_html = f'<div class="stats">{cells}</div>'
    bullets_html = ""
    if bullets:
        items = "".join(f'<li>{b}</li>' for b in bullets)
        bullets_html = f'<ul class="bl">{items}</ul>'
    caption = slide.get("caption", "")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{p['bg']};font-family:"Segoe UI",Arial,sans-serif;color:{p['text']}}}
.stage{{position:relative;width:{W}px;height:{H}px;padding:84px 96px 300px}}
.brand{{font-size:26px;font-weight:800;letter-spacing:.02em;color:{p['text']};opacity:.85}}
.kicker{{margin-top:18px;font-size:26px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{p['accent']}}}
h1{{margin-top:20px;font-size:78px;line-height:1.12;letter-spacing:-.02em;font-weight:800;max-width:1600px}}
h1.small{{font-size:62px}}
.stats{{display:flex;gap:26px;margin-top:56px}}
.stat{{flex:1;background:{p['surface']};border:1px solid {p['border']};border-radius:22px;padding:34px 30px;box-shadow:0 10px 28px rgba(16,24,40,.07)}}
.sv{{font-size:64px;font-weight:800;color:{p['accent']};line-height:1.05;letter-spacing:-.02em}}
.sl{{margin-top:14px;font-size:26px;font-weight:700;color:{p['text']}}}
.sn{{margin-top:8px;font-size:21px;color:{p['muted']};line-height:1.35}}
.bl{{margin-top:52px;list-style:none}}
.bl li{{position:relative;padding-left:44px;margin-bottom:30px;font-size:34px;line-height:1.4;color:#28323d}}
.bl li::before{{content:"";position:absolute;left:0;top:16px;width:18px;height:18px;border-radius:5px;background:{p['primary']}}}
.cap{{position:absolute;left:96px;right:96px;bottom:78px;background:rgba(22,32,44,.93);
  border-radius:20px;padding:30px 40px;display:flex;align-items:center}}
.cap p{{color:#fff;font-size:37px;line-height:1.36;font-weight:500;max-width:1560px}}
.pg{{position:absolute;right:96px;bottom:300px;font-size:22px;color:{p['muted2']};font-weight:700;letter-spacing:.08em}}
</style></head><body><div class="stage">
<div class="brand">{brand}</div>
<div class="kicker">{slide.get('kicker','')}</div>
<h1 class="{'small' if slide.get('small') else ''}">{slide['headline']}</h1>
{stats_html}{bullets_html}
<div class="pg">{idx:02d} / {total:02d}</div>
</div><div class="cap"><p>{caption}</p></div></body></html>"""


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(map(str,cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def dur_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


async def tts(text, out_path):
    import edge_tts
    c = edge_tts.Communicate(text, VOICE)
    await c.save(str(out_path))


def srt_ts(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    spec_path, out_dir = sys.argv[1], Path(sys.argv[2])
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    work = out_dir / ("_work-" + spec["slug"])
    (work / "png").mkdir(parents=True, exist_ok=True)
    (work / "aud").mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    slides = spec["slides"]
    n = len(slides)
    print(f"slides: {n}")

    # 1. HTML + PNG
    for i, s in enumerate(slides, 1):
        hp = work / f"slide{i:02d}.html"
        hp.write_text(html_for(s, i, n, spec.get("brand", "SERVERBUDGET")), encoding="utf-8")
        png = work / "png" / f"slide{i:02d}.png"
        run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", f"--window-size={W},{H}",
             "--user-data-dir=" + str(work / "chrome-profile"),
             f"--screenshot={png}", hp.as_uri()])
        if not png.exists():
            raise RuntimeError("no screenshot for slide " + str(i))
        print(f"  png {i}: {png.stat().st_size//1024} KB")

    # 2. narration
    for i, s in enumerate(slides, 1):
        mp3 = work / "aud" / f"slide{i:02d}.mp3"
        asyncio.run(tts(s["caption"], mp3))
        print(f"  tts {i}: {dur_of(mp3):.2f}s")

    # 3. segments
    segs, srt, t = [], [], 0.0
    for i, s in enumerate(slides, 1):
        png = work / "png" / f"slide{i:02d}.png"
        mp3 = work / "aud" / f"slide{i:02d}.mp3"
        d = dur_of(mp3) + 0.55
        seg = work / f"seg{i:02d}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-i", str(mp3),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-tune", "stillimage",
             "-r", "30", "-vf", f"scale={W}:{H},format=yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
             "-t", f"{d:.2f}", str(seg)])
        segs.append(seg)
        srt.append(f"{i}\n{srt_ts(t)} --> {srt_ts(t + d - 0.05)}\n{s['caption']}\n")
        t += d

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    silent = work / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    # 4. finalise. The narration line is already on screen as a lower-third
    # caption bar, so burning the SRT on top would double the text. Ship the
    # SRT alongside instead and upload it as the caption track.
    srt_path = out_dir / (spec["slug"] + ".srt")
    srt_path.write_text("\n".join(srt), encoding="utf-8")
    final = out_dir / (spec["slug"] + ".mp4")
    run(["ffmpeg", "-y", "-i", str(silent), "-c", "copy", "-movflags", "+faststart", str(final)])

    d = dur_of(final)
    print(f"\nFINAL {final}  {d:.1f}s  {final.stat().st_size/1024/1024:.1f} MB")
    if d < 30 or d > 60:
        print(f"WARNING: duration {d:.1f}s outside the 30-60s target")


if __name__ == "__main__":
    main()
