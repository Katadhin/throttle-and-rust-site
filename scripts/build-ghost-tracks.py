#!/usr/bin/env python3
"""Generate the /ghost-tracks/ section from data/ghost-tracks.json.

One source of truth. Add an entry to the JSON, re-run this, commit the output.

    python3 scripts/build-ghost-tracks.py

Writes ghost-tracks/index.html plus ghost-tracks/<slug>/index.html for every
entry, and rewrites the ghost-track block in sitemap.xml.

House rules this generator enforces, because the pages are permanent and the
social posts they come from were not:
  - No byline anywhere. The section is an unattributed record.
  - Generated art only, never archive photography. That is a rights problem on
    this domain which the ephemeral social channel does not have.
  - Two art lanes. Lane 1 is textless ephemera (a stub, a program, weeds in
    asphalt), shot photographically, never depicting a track. Lane 2 may depict
    the track itself and is opted into with "imagined": true on the entry.
  - Lane 2 art must carry a disclaimer burned into the image by
    scripts/label-imagined.py before it is placed. The risk was never a picture
    of a track, it was a picture that could pass as evidence of one while
    sitting above that entry's own citations, and a page caption does not
    survive being scraped into a social card or screenshotted. Caption for
    readers, pixels for everyone else.
  - No lettering in any generated frame, no faces or people, no identifiable
    liveries or numbers, no logos.
  - Images are optional and self-healing. An entry with no "image" key, or one
    whose file is not on disk yet, renders text-only and prints a warning.
  - Every entry carries its sources.
"""

import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ghost-tracks.json")
OUT = os.path.join(ROOT, "ghost-tracks")
SITE = "https://throttleandrust.com"

# Section banner. Doubles as the default social card for any entry with no art
# of its own. Textless ephemera, no track depicted — see the house rules above.
BANNER = "/images/ghost-tracks-banner.jpg"
BANNER_ALT = ("A folded, sun-bleached race program on a truck dash, print worn "
              "past reading, late afternoon light through the windshield.")

# Stands under every image in this section. The register's whole credibility is
# that its claims are sourced, so the art has to say out loud that it is not one
# of the sources.
DISCLAIM = "Illustration. Not an archive photograph."

# Used instead of DISCLAIM when an entry sets "imagined": true, which marks art
# depicting the track itself rather than an object.
#
# This caption is the second line of defence, not the first. Any imagined track
# image must also carry the label burned into its pixels by
# scripts/label-imagined.py, because this text does not survive being scraped
# into a social card, screenshotted, or reposted, and those are the normal ways
# these images travel. Caption for readers, pixels for everyone else.
#
# Kept short because imagined-lane captions are now plate titles that already
# end in "Imagined" ("Turn Three, Imagined"), so restating it here would be the
# third time on one page. The burned-in bar carries the full sentence.
DISCLAIM_IMAGINED = "Not an archive photograph."


def caption_with(caption, stamp):
    """Join a caption to its disclaimer stamp with sane punctuation.

    Imagined-lane captions are plate titles ("Turn Three, Imagined") and carry
    no terminal punctuation, so a bare space ran them into the stamp.
    """
    if not caption:
        return stamp
    caption = caption.strip()
    if caption[-1] not in ".!?":
        caption += "."
    return f"{caption} {stamp}"


STATE_NAMES = {
    "AL": "Alabama", "AR": "Arkansas", "CA": "California", "FL": "Florida",
    "GA": "Georgia", "IL": "Illinois", "MD": "Maryland", "NC": "North Carolina",
    "NH": "New Hampshire", "NJ": "New Jersey", "NY": "New York",
    "PA": "Pennsylvania", "SC": "South Carolina", "TN": "Tennessee",
    "TX": "Texas", "VA": "Virginia",
}


def years_of(entry):
    """Every four-digit year mentioned in an entry's era string.

    Era is free text and deliberately varied ("Eight Cup races, 1958-1968",
    "Closed 1958 - demolished 1967", "Twenty-eight Cup races, 1950s-1971"), so
    this reads years out rather than expecting a schema. One entry has no year
    at all, which is why callers must handle an empty result.
    """
    return [int(y) for y in re.findall(r"(?:19|20)\d{2}", entry.get("era", ""))]


def span_of(entry):
    """(first year, last year) an entry covers, or None if no year is recorded.

    Matching on the opening decade alone was wrong: Langhorne ran 1926 to 1971
    and got filed by itself in the 1920s, which left its page a dead end while
    it in fact overlapped nearly every other track in the register. Spans
    overlap, decades do not.
    """
    ys = years_of(entry)
    return (min(ys), max(ys)) if ys else None


def overlaps(a, b):
    return a and b and a[0] <= b[1] and b[0] <= a[1]


def related(entry, entries, limit=4):
    """Cross-links by state and by decade, derived purely from existing data.

    A register that can only be walked in posting order is a list, not a
    reference. These two axes are the ones a reader actually arrives with:
    somewhere near me, or somewhere from the same stretch of years. Nothing here
    asserts a new fact, so it costs no sourcing.
    """
    blocks = []

    same_state = [x for x in entries
                  if x["state"] == entry["state"] and x["slug"] != entry["slug"]]
    if same_state:
        label = "Elsewhere in %s" % STATE_NAMES.get(entry["state"], entry["state"])
        blocks.append((label, same_state[:limit]))

    span = span_of(entry)
    if span:
        # Closest overlap first, so a 1926-1971 track leads with contemporaries
        # rather than whatever happens to sit at the top of the file.
        mid = (span[0] + span[1]) / 2
        concurrent = [x for x in entries
                      if x["slug"] != entry["slug"] and x["state"] != entry["state"]
                      and overlaps(span, span_of(x))]
        concurrent.sort(key=lambda x: abs(sum(span_of(x)) / 2 - mid))
        if concurrent:
            blocks.append(("Running at the same time", concurrent[:limit]))

    if not blocks:
        return ""

    e = html.escape
    out = ['<div class="related">']
    for label, items in blocks:
        links = " &nbsp;&middot;&nbsp; ".join(
            f'<a href="/ghost-tracks/{x["slug"]}/">{e(x["name"])}</a>' for x in items)
        out.append(f'<div class="related-row">'
                   f'<span class="related-label">{e(label)}</span>{links}</div>')
    out.append("</div>")
    return "".join(out)


def have(path):
    """True if a site-root-relative image path exists on disk."""
    return bool(path) and os.path.isfile(os.path.join(ROOT, path.lstrip("/")))


def jpeg_size(path):
    """(width, height) of a JPEG, read from its headers. None if unreadable.

    Pure stdlib on purpose. This generator has never needed Pillow and should
    not start: it runs on whatever machine happens to be doing a deploy.

    Worth emitting because Facebook will defer rendering a card while it goes
    and fetches an image whose dimensions it was not told, which shows up as a
    share with no picture on the first post and a correct one later.
    """
    try:
        with open(os.path.join(ROOT, path.lstrip("/")), "rb") as f:
            if f.read(2) != b"\xff\xd8":
                return None
            while True:
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if not marker:
                    return None
                if marker[0] in range(0xC0, 0xCF) and marker[0] not in (0xC4, 0xC8, 0xCC):
                    f.read(3)
                    h = int.from_bytes(f.read(2), "big")
                    w = int.from_bytes(f.read(2), "big")
                    return w, h
                length = int.from_bytes(f.read(2), "big")
                if length < 2:
                    return None
                f.seek(length - 2, 1)
    except OSError:
        return None

NAV = (
    '<span class="links"><a href="/journal/">Journal</a> &middot; '
    '<a href="/recipes/">Recipes</a> &middot; <a href="/places/">Places</a> &middot; '
    '<a href="/calendar/">Calendar</a> &middot; <a href="/ghost-tracks/">Ghost Tracks</a></span>'
)

SOCIAL = (
    '<a href="https://www.facebook.com/throttleandrust/" target="_blank" rel="noopener">Facebook</a> · '
    '<a href="https://www.instagram.com/throttleandrust/" target="_blank" rel="noopener">Instagram</a> · '
    '<a href="https://www.tiktok.com/@throttleandrust" target="_blank" rel="noopener">TikTok</a> · '
    '<a href="https://x.com/throttleandrust" target="_blank" rel="noopener">X</a> · '
    '<a href="https://www.youtube.com/@Throttle_and_Rust" target="_blank" rel="noopener">YouTube</a>'
)

CSS = """
  :root {
    --bg: #f3eddf; --bg-deep: #ebe3d1; --ink: #1c1f26; --ink-soft: #4a4d55;
    --ink-faint: #8a8c92; --rust: #a23b1f; --max-width: 620px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg); color: var(--ink);
    font-family: 'IBM Plex Mono', monospace; font-weight: 400;
    line-height: 1.7; font-size: 15px;
    -webkit-font-smoothing: antialiased; overflow-x: hidden;
  }
  body::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E");
    opacity: 0.06; mix-blend-mode: multiply;
  }
  .topbar {
    position: relative; z-index: 10; padding: 22px 32px; display: flex;
    justify-content: space-between; align-items: center; max-width: 980px;
    margin: 0 auto; font-size: 11px; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--ink-soft); gap: 16px; flex-wrap: wrap;
  }
  .topbar .place-brand, .topbar .links { font-family: 'Special Elite', monospace; }
  .topbar a { color: var(--ink-soft); text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 0.2s ease; }
  .topbar a:hover { border-bottom-color: var(--ink-soft); }
  .container { max-width: var(--max-width); margin: 0 auto; padding: 32px 24px 0; position: relative; z-index: 2; }
  .header { text-align: center; margin: 24px 0 52px; }
  .header-eyebrow {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.3em;
    text-transform: uppercase; color: var(--rust); margin-bottom: 12px;
  }
  .header-title {
    font-family: 'Playfair Display', serif; font-style: italic; font-weight: 400;
    font-size: clamp(32px, 5vw, 44px); color: var(--ink); line-height: 1.2;
  }
  .header-sub {
    margin-top: 18px; font-size: 14px; color: var(--ink-soft);
    font-style: italic; font-family: 'Playfair Display', serif;
  }
  .lead { border-top: 2px solid var(--rust); padding: 26px 0 38px; }
  .lead-label {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.25em;
    text-transform: uppercase; color: var(--rust); margin-bottom: 14px;
  }
  .lead-name { font-family: 'Playfair Display', serif; font-style: italic; font-size: 30px; line-height: 1.25; margin-bottom: 8px; }
  .lead-name a { color: var(--ink); text-decoration: none; border-bottom: 1px solid rgba(28,31,38,0.25); }
  .lead-name a:hover { border-bottom-color: var(--rust); color: var(--rust); }
  .meta {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--ink-faint); margin-bottom: 16px;
  }
  .lead-body { font-size: 15px; line-height: 1.75; color: var(--ink-soft); }
  .lead-art { margin: 20px 0 22px; }
  .related { margin: 34px 0 6px; border-top: 1px solid rgba(28, 31, 38, 0.15); padding-top: 20px; }
  .related-row { margin-bottom: 12px; font-size: 13.5px; line-height: 1.8; }
  .related-row:last-child { margin-bottom: 0; }
  .related-label {
    display: block; font-family: 'Special Elite', monospace; font-size: 10.5px;
    letter-spacing: 0.22em; text-transform: uppercase; color: var(--ink-faint);
    margin-bottom: 4px;
  }
  .related a { color: var(--ink-soft); text-decoration: none; border-bottom: 1px solid rgba(28, 31, 38, 0.2); }
  .related a:hover { color: var(--rust); border-bottom-color: var(--rust); }
  .row-thumb { flex: 0 0 96px; display: block; }
  .row-thumb img { display: block; width: 96px; height: 64px; object-fit: cover;
    border: 1px solid rgba(28, 31, 38, 0.18);
    filter: saturate(0.94) contrast(0.97); }
  .row-thumb.is-empty { border: none; }
  .register-label {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.25em;
    text-transform: uppercase; color: var(--ink-faint); margin: 46px 0 6px;
  }
  .row { padding: 20px 0; border-bottom: 1px solid rgba(28, 31, 38, 0.15); display: flex; gap: 18px; align-items: baseline; }
  .row:last-child { border-bottom: none; }
  .row-state {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.14em;
    color: var(--rust); flex: 0 0 30px; padding-top: 4px;
  }
  .row-main { flex: 1 1 auto; min-width: 0; }
  .row-name { font-family: 'Playfair Display', serif; font-weight: 500; font-size: 20px; line-height: 1.3; margin-bottom: 4px; }
  .row-name a { color: var(--ink); text-decoration: none; border-bottom: 1px solid transparent; }
  .row-name a:hover { color: var(--rust); border-bottom-color: var(--rust); }
  .row-meta { font-family: 'Special Elite', monospace; font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--ink-faint); }
  .art { margin: 0 0 8px; }
  .art img {
    display: block; width: 100%; height: auto;
    border: 1px solid rgba(28, 31, 38, 0.18);
    filter: saturate(0.94) contrast(0.97);
  }
  .art figcaption {
    margin-top: 10px; font-family: 'Playfair Display', serif; font-style: italic;
    font-size: 12.5px; line-height: 1.6; color: var(--ink-faint);
  }
  .banner { max-width: var(--max-width); margin: 0 auto 44px; padding: 0 24px; position: relative; z-index: 2; }
  .entry-art { margin: 26px 0 34px; }
  .entry-title { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 400; font-size: clamp(30px, 5vw, 40px); line-height: 1.18; color: var(--ink); margin-bottom: 14px; }
  .entry-body { font-size: 16px; line-height: 1.8; color: var(--ink); margin-top: 30px; }
  .entry-body p { margin-bottom: 1.5em; }
  .rule { border: none; border-top: 1px solid rgba(28, 31, 38, 0.18); margin: 44px 0 26px; }
  .sources-label {
    font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.25em;
    text-transform: uppercase; color: var(--ink-faint); margin-bottom: 12px;
  }
  .sources { list-style: none; font-size: 12.5px; line-height: 1.9; word-break: break-word; }
  .sources a { color: var(--ink-soft); text-decoration: none; border-bottom: 1px solid rgba(28,31,38,0.2); }
  .sources a:hover { color: var(--rust); border-bottom-color: var(--rust); }
  .note { margin-top: 18px; font-size: 12.5px; font-style: italic; font-family: 'Playfair Display', serif; color: var(--ink-faint); }
  .pager { display: flex; justify-content: space-between; gap: 20px; margin-top: 46px; font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; }
  .pager a { color: var(--rust); text-decoration: none; border-bottom: 1px solid transparent; max-width: 46%; }
  .pager a:hover { border-bottom-color: var(--rust); }
  .pager .spacer { flex: 1 1 auto; }
  .back { display: block; text-align: center; margin-top: 42px; font-family: 'Special Elite', monospace; font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--ink-faint); text-decoration: none; }
  .back:hover { color: var(--rust); }
  .tail { margin-top: 54px; padding-top: 24px; border-top: 1px solid rgba(28,31,38,0.15); font-size: 13px; color: var(--ink-faint); font-style: italic; font-family: 'Playfair Display', serif; text-align: center; }
  footer { margin-top: 90px; padding: 36px 32px 32px; position: relative; z-index: 2; }
  .footer-inner {
    max-width: 980px; margin: 0 auto; border-top: 1px solid var(--ink); padding-top: 28px;
    display: flex; justify-content: space-between; align-items: center; font-size: 11px;
    letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-soft);
    font-family: 'Special Elite', monospace; flex-wrap: wrap; gap: 12px;
  }
  .footer-inner a { color: var(--ink-soft); text-decoration: none; border-bottom: 1px solid transparent; }
  .footer-inner a:hover { border-bottom-color: var(--ink-soft); }
  .footer-right { text-align: right; line-height: 2; }
  @media (max-width: 600px) {
    .topbar { padding: 18px 20px; font-size: 10px; letter-spacing: 0.1em; }
    .lead-name { font-size: 25px; }
    .row { gap: 12px; }
    .row-thumb { flex-basis: 64px; }
    .row-thumb img { width: 64px; height: 44px; }
    .footer-inner { flex-direction: column; align-items: flex-start; }
    .footer-right { text-align: left; }
  }
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
         '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400'
         '&family=IBM+Plex+Mono:wght@300;400;500&family=Special+Elite&display=swap" rel="stylesheet" />')

ICONS = """<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png" />
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta name="theme-color" content="#1c1f26" />"""


def shell(title, desc, url, body, image=None, image_alt=None):
    e = html.escape
    card = ""
    if have(image):
        card = (f'\n<meta property="og:image" content="{SITE}{image}" />'
                f'\n<meta property="og:image:secure_url" content="{SITE}{image}" />'
                f'\n<meta property="og:image:type" content="image/jpeg" />'
                f'\n<meta name="twitter:card" content="summary_large_image" />')
        dims = jpeg_size(image)
        if dims:
            card += (f'\n<meta property="og:image:width" content="{dims[0]}" />'
                     f'\n<meta property="og:image:height" content="{dims[1]}" />')
        if image_alt:
            card += (f'\n<meta property="og:image:alt" content="{e(image_alt)}" />'
                     f'\n<meta name="twitter:image:alt" content="{e(image_alt)}" />')
    else:
        # No art on disk means no large card. Summary still beats a bare link.
        card = '\n<meta name="twitter:card" content="summary" />'
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
{ICONS}
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Throttle &amp; Rust" />
<meta property="og:title" content="{e(title)}" />
<meta property="og:description" content="{e(desc)}" />
<meta property="og:url" content="{url}" />{card}
{FONTS}
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="place-brand"><a href="/">Throttle &amp; Rust</a></span>
  {NAV}
</div>

{body}

<footer>
  <div class="footer-inner">
    <div class="footer-left"><a href="/">Throttle &amp; Rust</a></div>
    <div class="footer-right">
      <span class="footer-social">{SOCIAL}</span><br />
      <span class="credit">site by the Meg</span> &middot; 2026 &middot; <a href="/about/#how-this-is-made">How this is made</a>
    </div>
  </div>
</footer>

</body>
</html>
"""
    # optional blocks leave gaps behind when they are empty
    return re.sub(r"\n{3,}", "\n\n", page)


def detail(entry, prev_e, next_e, entries=()):
    e = html.escape
    paras = "".join(f"<p>{e(p)}</p>" for p in re.split(r"\n{2,}", entry["body"].strip()))
    srcs = "".join(
        f'<li><a href="{s}" target="_blank" rel="noopener nofollow">{e(s)}</a></li>'
        for s in entry["sources"])
    note = f'<div class="note">Note: {e(entry["note"])}.</div>' if entry.get("note") else ""

    art, img = "", entry.get("image")
    if img and not have(img):
        print("  warning: %s references %s, which is not on disk — rendering text-only"
              % (entry["slug"], img))
    elif img:
        stamp = DISCLAIM_IMAGINED if entry.get("imagined") else DISCLAIM
        cap = caption_with(e(entry["caption"]) if entry.get("caption") else "", stamp)
        art = (f'<figure class="art entry-art"><img src="{img}" alt="{e(entry.get("alt", ""))}" '
               f'loading="lazy" /><figcaption>{cap}</figcaption></figure>')

    rel = related(entry, entries)

    pager = '<div class="pager">'
    pager += (f'<a href="/ghost-tracks/{prev_e["slug"]}/">&larr; {e(prev_e["name"])}</a>'
              if prev_e else '<span class="spacer"></span>')
    pager += (f'<a href="/ghost-tracks/{next_e["slug"]}/">{e(next_e["name"])} &rarr;</a>'
              if next_e else '<span class="spacer"></span>')
    pager += "</div>"

    body = f"""<div class="container">
  <div class="header-eyebrow" style="margin-top:26px;">Ghost tracks</div>
  <h1 class="entry-title">{e(entry['name'])}</h1>
  <div class="meta">{e(entry['place'])} &nbsp;&middot;&nbsp; {e(entry['era'])}</div>
  {art}

  <div class="entry-body">{paras}</div>

  <hr class="rule" />
  <div class="sources-label">Sources</div>
  <ul class="sources">{srcs}</ul>
  {note}

  {rel}

  {pager}
  <a class="back" href="/ghost-tracks/">&larr; The whole register</a>
</div>"""
    desc = entry["body"].strip().split(". ")[0][:180]
    return shell(f"{entry['name']} — Ghost Tracks — Throttle & Rust", desc,
                 f"{SITE}/ghost-tracks/{entry['slug']}/", body,
                 image=img if have(img) else BANNER,
                 image_alt=entry.get("alt") if have(img) else BANNER_ALT)


def rows_html(items):
    """The register row list, shared by the main index and the browse pages.

    The thumbnail column switches itself on once at least two of the listed
    entries are illustrated, and stays off until then. Rows without art get an
    invisible spacer rather than a box, so a sparse column reads as a consistent
    indent that fills in over time instead of a grid full of holes. One lone
    thumbnail looked like a mistake, which is why the floor is two.
    """
    e = html.escape
    thumbs_on = sum(1 for x in items if have(x.get("image"))) >= 2

    def row_thumb(x):
        if not thumbs_on:
            return ""
        if have(x.get("image")):
            return (f'<a class="row-thumb" href="/ghost-tracks/{x["slug"]}/" tabindex="-1" '
                    f'aria-hidden="true"><img src="{x["image"]}" alt="" loading="lazy" /></a>')
        return '<div class="row-thumb is-empty"></div>'

    return "".join(f"""
    <div class="row">
      <div class="row-state">{e(x['state'])}</div>{row_thumb(x)}
      <div class="row-main">
        <div class="row-name"><a href="/ghost-tracks/{x['slug']}/">{e(x['name'])}</a></div>
        <div class="row-meta">{e(x['place'])} &nbsp;&middot;&nbsp; {e(x['era'])}</div>
      </div>
    </div>""" for x in items)


def browse_groups(entries):
    """(states, decades) worth their own page.

    A state page needs at least two entries. A one-entry state page is a thin
    page that answers a query worse than the entry itself does, so those states
    are simply left to the register and the cross-links.

    Decades use overlapping spans, so a track that ran 1926 to 1971 appears on
    every decade page it was actually open for, rather than only its first.
    """
    states = {}
    for x in entries:
        states.setdefault(x["state"], []).append(x)
    states = {k: v for k, v in states.items() if len(v) >= 2}

    decades = {}
    for x in entries:
        span = span_of(x)
        if not span:
            continue
        for d in range((span[0] // 10) * 10, (span[1] // 10) * 10 + 10, 10):
            decades.setdefault(d, []).append(x)

    # Decades need a higher floor than states, and for a different reason.
    # Because long-lived tracks appear on every decade they were open, the tail
    # decades filled with the same handful of entries over and over: the 1990s,
    # 2000s, 2010s and 2020s pages were an identical pair of tracks four times.
    # State pages with two entries are at least unique to each other. Adjacent
    # decade pages with two entries are the same page with a different heading,
    # which is thin and duplicative. Those tracks still appear on the busier
    # decade pages their spans cover, so nothing is lost by dropping the tails.
    decades = {k: v for k, v in decades.items() if len(v) >= 4}

    return states, decades


def chrono(items):
    """Oldest first. Posting order means nothing to a reader of a reference."""
    return sorted(items, key=lambda x: (span_of(x) or (9999, 9999))[0])


def browse_page(kind, key, items, total):
    e = html.escape
    if kind == "state":
        name = STATE_NAMES.get(key, key)
        title = "%s — Ghost Tracks" % name
        eyebrow = "Ghost tracks"
        heading = name
        sub = ("%d tracks in %s that held a national-series stock car race and "
               "do not run anymore." % (len(items), name))
        url = "%s/ghost-tracks/state/%s/" % (SITE, key.lower())
    else:
        title = "The %ss — Ghost Tracks" % key
        eyebrow = "Ghost tracks"
        heading = "The %ss" % key
        sub = ("%d tracks in this record were open at some point during the "
               "%ss." % (len(items), key))
        url = "%s/ghost-tracks/era/%ss/" % (SITE, key)

    body = f"""<div class="container">
  <div class="header">
    <div class="header-eyebrow">{eyebrow}</div>
    <div class="header-title">{e(heading)}</div>
    <div class="header-sub">{e(sub)}</div>
  </div>

  <div class="register-label">{len(items)} of {total}</div>
  {rows_html(chrono(items))}

  <div class="tail"><a class="back" href="/ghost-tracks/">&larr; The whole register</a></div>
</div>"""
    return shell(title + " — Throttle & Rust", sub, url, body,
                 image=BANNER, image_alt=BANNER_ALT)


def browse_block(states, decades):
    """The browse rail on the main register page."""
    e = html.escape
    st = " &nbsp;&middot;&nbsp; ".join(
        f'<a href="/ghost-tracks/state/{k.lower()}/">{e(STATE_NAMES.get(k, k))} ({len(v)})</a>'
        for k, v in sorted(states.items(), key=lambda kv: (-len(kv[1]), kv[0])))
    de = " &nbsp;&middot;&nbsp; ".join(
        f'<a href="/ghost-tracks/era/{k}s/">{k}s ({len(v)})</a>'
        for k, v in sorted(decades.items()))
    return (f'<div class="related browse">'
            f'<div class="related-row"><span class="related-label">By state</span>{st}</div>'
            f'<div class="related-row"><span class="related-label">By decade</span>{de}</div>'
            f'</div>')


def index(entries):
    e = html.escape
    lead, rest = entries[0], entries[1:]
    rows = rows_html(rest)
    states, decades = browse_groups(entries)
    browse = browse_block(states, decades)

    # Art for the featured entry, shown in the lead block. Same self-healing
    # rule as everywhere else: missing file means the lead renders text-only.
    lead_img = lead.get("image")
    lead_art = ""
    if have(lead_img):
        stamp = DISCLAIM_IMAGINED if lead.get("imagined") else DISCLAIM
        cap = caption_with(e(lead["caption"]) if lead.get("caption") else "", stamp)
        lead_art = (f'<figure class="art lead-art"><img src="{lead_img}" '
                    f'alt="{e(lead.get("alt", ""))}" /><figcaption>{cap}</figcaption></figure>')

    banner = ""
    if have(BANNER):
        banner = (f'<div class="banner"><figure class="art">'
                  f'<img src="{BANNER}" alt="{e(BANNER_ALT)}" />'
                  f'<figcaption>{DISCLAIM}</figcaption></figure></div>')
    else:
        print("  warning: banner %s is not on disk — index rendering without it" % BANNER)

    body = f"""<div class="container">
  <div class="header">
    <div class="header-eyebrow">Ghost tracks</div>
    <div class="header-title">Tracks that are gone.</div>
    <div class="header-sub">Places that held a national-series stock car race and do not run anymore. The record on most of them is thin, so it gets kept here.</div>
  </div>
</div>

{banner}

<div class="container" style="padding-top:0;">

  <div class="lead">
    <div class="lead-label">This week</div>
    <div class="lead-name"><a href="/ghost-tracks/{lead['slug']}/">{e(lead['name'])}</a></div>
    <div class="meta">{e(lead['place'])} &nbsp;&middot;&nbsp; {e(lead['era'])}</div>
    {lead_art}
    <div class="lead-body">{e(lead['body'])}</div>
  </div>

  {browse}

  <div class="register-label">The register &middot; {len(entries)} tracks</div>
  {rows}

  <div class="tail">Every one of these had a last race that nobody in the stands knew was the last one.</div>
</div>"""
    # The section's share card follows the featured entry when that entry has
    # art, so a link to /ghost-tracks/ posted this week looks like this week.
    # Falls back to the standing banner otherwise.
    card_img = lead_img if have(lead_img) else BANNER
    card_alt = lead.get("alt") if have(lead_img) else BANNER_ALT
    return shell("Ghost Tracks — Throttle & Rust",
                 "A register of racetracks that held a national-series stock car race and do not run anymore.",
                 f"{SITE}/ghost-tracks/", body, image=card_img, image_alt=card_alt)


def sitemap(entries, states=None, decades=None):
    path = os.path.join(ROOT, "sitemap.xml")
    xml = open(path).read()
    xml = re.sub(r"\s*<url>\s*<loc>https://throttleandrust\.com/ghost-tracks/[^<]*</loc>.*?</url>",
                 "", xml, flags=re.S)
    block = "\n  <url>\n    <loc>%s/ghost-tracks/</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (
        SITE, entries[0]["first"])
    for x in entries:
        block += "\n  <url>\n    <loc>%s/ghost-tracks/%s/</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (
            SITE, x["slug"], x["first"])
    newest = entries[0]["first"]
    for code in sorted(states or {}):
        block += "\n  <url>\n    <loc>%s/ghost-tracks/state/%s/</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (
            SITE, code.lower(), newest)
    for dec in sorted(decades or {}):
        block += "\n  <url>\n    <loc>%s/ghost-tracks/era/%ss/</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (
            SITE, dec, newest)
    xml = xml.replace("</urlset>", block + "\n</urlset>")
    open(path, "w").write(xml)
    return len(entries) + 1 + len(states or {}) + len(decades or {})


def homepage(entries):
    """Fill the ghost-track-of-the-week block on the homepage."""
    e = html.escape
    x = entries[0]
    path = os.path.join(ROOT, "index.html")
    src = open(path).read()
    block = f"""<!-- GHOST:START -->
  <div class="upcoming" style="max-width:580px;margin:56px auto 0;padding:0 20px;text-align:center;">
    <div style="font-family:'Special Elite',monospace;font-size:11px;letter-spacing:0.3em;text-transform:uppercase;color:#a23b1f;margin-bottom:14px;"><a href="/ghost-tracks/" style="color:#a23b1f;text-decoration:none;border-bottom:1px solid rgba(162,59,31,0.35);">Ghost track of the week</a></div>
    <div style="font-family:'Playfair Display',serif;font-style:italic;font-size:24px;line-height:1.35;color:#1c1f26;margin-bottom:6px;"><a href="/ghost-tracks/{x['slug']}/" style="color:#1c1f26;text-decoration:none;">{e(x['name'])}</a></div>
    <div style="font-family:'Special Elite',monospace;font-size:10.5px;letter-spacing:0.18em;text-transform:uppercase;color:#8a8c92;margin-bottom:12px;">{e(x['place'])} &middot; {e(x['era'])}</div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;color:#4a4d55;line-height:1.65;">{e(x['body'])}</div>
  </div>
  <!-- GHOST:END -->"""
    if "<!-- GHOST:START -->" not in src or "<!-- GHOST:END -->" not in src:
        print("  warning: GHOST markers missing from index.html, homepage not updated")
        return
    new = re.sub(r"<!-- GHOST:START -->.*?<!-- GHOST:END -->", lambda _: block, src, flags=re.S)
    if new != src:
        open(path, "w").write(new)


def main():
    entries = json.load(open(DATA))
    entries.sort(key=lambda x: x["first"], reverse=True)
    os.makedirs(OUT, exist_ok=True)

    open(os.path.join(OUT, "index.html"), "w").write(index(entries))

    for i, x in enumerate(entries):
        d = os.path.join(OUT, x["slug"])
        os.makedirs(d, exist_ok=True)
        prev_e = entries[i - 1] if i > 0 else None
        next_e = entries[i + 1] if i + 1 < len(entries) else None
        open(os.path.join(d, "index.html"), "w").write(detail(x, prev_e, next_e, entries))

    states, decades = browse_groups(entries)
    for code, items in states.items():
        d = os.path.join(OUT, "state", code.lower())
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(
            browse_page("state", code, items, len(entries)))
    for dec, items in decades.items():
        d = os.path.join(OUT, "era", "%ss" % dec)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(
            browse_page("era", dec, items, len(entries)))

    # state/ and era/ are wholly generated, so anything there this run did not
    # write is left over from an older grouping rule. Stale pages stay live on
    # Pages, unlinked and out of the sitemap, so remove them.
    keep = {"state": {c.lower() for c in states}, "era": {"%ss" % d for d in decades}}
    for sub, wanted in keep.items():
        base = os.path.join(OUT, sub)
        for name in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if name not in wanted and os.path.isdir(os.path.join(base, name)):
                shutil.rmtree(os.path.join(base, name))
                print("  removed stale %s/%s/" % (sub, name))

    homepage(entries)
    n = sitemap(entries, states, decades)
    print("ghost-tracks: %d detail pages + index, %d state pages, %d decade pages, "
          "%d sitemap urls, homepage block set to %s"
          % (len(entries), len(states), len(decades), n, entries[0]["slug"]))


if __name__ == "__main__":
    main()
