#!/usr/bin/env python3
"""
Keep /videos/ in step with the Throttle & Rust YouTube channel.

    python3 scripts/update-videos.py            pull the channel feed, merge, render
    python3 scripts/update-videos.py --render   re-render from data/videos.json only

The channel feed only carries the newest 15 uploads, so every video ever seen is
kept in data/videos.json and the feed is merged into it. New videos get their
length, date and description from their watch page. The page is rendered from
scripts/videos-template.html into videos/index.html.

Run daily by .github/workflows/videos.yml. Stdlib only.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

CHANNEL_ID = "UCL3YelGWCYh_UClLot6cdiw"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/videos.json"
TEMPLATE = ROOT / "scripts/videos-template.html"
OUT = ROOT / "videos/index.html"
EPISODE_MIN_SECONDS = 5 * 60   # full PROfile interviews run 9 to 22 minutes; clips are under 3
CLIPS_SHOWN = 12
UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")


def watch_details(vid):
    page = fetch(f"https://www.youtube.com/watch?v={vid}")
    secs = re.search(r'"lengthSeconds":"(\d+)"', page)
    pub = re.search(r'"(?:publishDate|uploadDate)":"([^"]+)"', page)
    desc = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', page)
    out = {}
    if secs:
        s = int(secs.group(1))
        out["duration"] = f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"
    if pub:
        out["published"] = pub.group(1)[:10]
    if desc:
        out["description"] = json.loads(f'"{desc.group(1)}"')
    return out


def pull_feed(videos):
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    root = ET.fromstring(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"))
    known = {v["id"]: v for v in videos}
    added = 0
    for e in root.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        title = e.find("a:title", ns).text
        if vid in known:
            known[vid]["title"] = title  # titles get edited after upload
            continue
        v = {"id": vid, "title": title, "published": e.find("a:published", ns).text[:10], "duration": "", "description": ""}
        try:
            v.update(watch_details(vid))
        except Exception as err:
            print(f"! details for {vid}: {err}")
        videos.append(v)
        added += 1
        print(f"+ {v['published']} {title}")
    return added


def seconds(d):
    n = 0
    for part in (d or "0").split(":"):
        n = n * 60 + int(part)
    return n


def split_title(t):
    """'Topic | Guest | Show' -> ('Topic', 'Guest')"""
    parts = [p.strip() for p in t.split("|")]
    sub = next((p for p in parts[1:] if "Throttle" not in p and "PRO" not in p), "")
    return parts[0], sub


def blurb(desc, n=150):
    text = re.sub(r"\s+", " ", re.sub(r"https?://\S+|#\S+", "", desc or "")).strip()
    text = re.sub(r"^[^A-Za-z0-9\"“]+", "", text)  # leading emoji
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def card(v, cls="card"):
    title, sub = split_title(v["title"])
    e = html.escape
    return f'''      <a class="{cls}" href="https://www.youtube.com/watch?v={v["id"]}" data-id="{v["id"]}" data-title="{e(v["title"])}" target="_blank" rel="noopener">
        <span class="thumb"><img src="https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg" alt="" loading="lazy" /><span class="len">{e(v["duration"])}</span><span class="play" aria-hidden="true"></span></span>
        <span class="card-date">{nice_date(v["published"])}</span>
        <span class="card-title">{e(title)}</span>
        {f'<span class="card-sub">{e(sub)}</span>' if sub else ''}
      </a>'''


def render(videos):
    videos = sorted(videos, key=lambda v: (v["published"], v["id"]), reverse=True)
    episodes = [v for v in videos if seconds(v["duration"]) >= EPISODE_MIN_SECONDS]
    clips = [v for v in videos if seconds(v["duration"]) < EPISODE_MIN_SECONDS]
    feat = episodes[0] if episodes else videos[0]
    ft, fs = split_title(feat["title"])
    e = html.escape
    featured = f'''<div class="player"><iframe id="player" src="https://www.youtube-nocookie.com/embed/{feat["id"]}?rel=0" title="{e(feat["title"])}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>
    <div class="now">
      <div class="now-date" id="nowDate">{nice_date(feat["published"])}</div>
      <h2 class="now-title" id="nowTitle">{e(ft)}</h2>
      <p class="now-blurb" id="nowBlurb">{e(blurb(feat["description"], 260))}</p>
      <a class="now-link" id="nowLink" href="https://www.youtube.com/watch?v={feat["id"]}" target="_blank" rel="noopener">Watch on YouTube &rarr;</a>
    </div>'''
    clip_html = "\n".join(card(v, "card" + (" is-extra" if i >= CLIPS_SHOWN else "")) for i, v in enumerate(clips))
    blurbs = {v["id"]: {"date": nice_date(v["published"]), "title": split_title(v["title"])[0], "blurb": blurb(v["description"], 260)} for v in videos}
    page = TEMPLATE.read_text()
    for k, val in {
        "{{FEATURED}}": featured,
        "{{EPISODES}}": "\n".join(card(v) for v in episodes),
        "{{CLIPS}}": clip_html,
        "{{MORE_HIDDEN}}": "" if len(clips) > CLIPS_SHOWN else " hidden",
        "{{COUNT}}": str(len(videos)),
        "{{UPDATED}}": videos[0]["published"],
        "{{OG_IMAGE}}": f"https://i.ytimg.com/vi/{feat['id']}/hqdefault.jpg",
        "{{VIDEO_DATA}}": json.dumps(blurbs, ensure_ascii=False).replace("</", "<\\/"),
    }.items():
        page = page.replace(k, val)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page)
    print(f"rendered {len(episodes)} episodes, {len(clips)} clips -> {OUT.relative_to(ROOT)}")


def main():
    videos = json.loads(DATA.read_text()) if DATA.exists() else []
    if "--render" not in sys.argv:
        added = pull_feed(videos)
        print(f"{added} new video(s)")
        videos.sort(key=lambda v: (v["published"], v["id"]), reverse=True)
        DATA.write_text(json.dumps(videos, indent=1, ensure_ascii=False) + "\n")
    render(videos)


if __name__ == "__main__":
    main()
