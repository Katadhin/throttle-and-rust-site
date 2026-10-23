#!/usr/bin/env python3
"""Generate a Ghost Tracks "imagined" image from the Gemini / Imagen API,
label it, and (optionally) wire it into the register and rebuild.

This is the hands-off version of what we were doing by hand in the Gemini web
app: no browser, no download, no filename guessing. The model returns the
image straight into the response; this script saves it, burns the "imagined"
disclaimer into the pixels with label-imagined.py, and gives it a natural,
searchable name from the start.

Runs on YOUR Mac, where the network is open. The cloud session can't reach
Google's API host; your machine can.

------------------------------------------------------------------------------
ONE-TIME SETUP
------------------------------------------------------------------------------
1. Get a key (free): https://aistudio.google.com/apikey
2. Put it in your shell, or in a gitignored file next to this script:

       export GEMINI_API_KEY="xxxx"
   or
       echo "xxxx" > scripts/.gemini_key      # already gitignored

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
Generate + label only (review before deploy):

    python3 scripts/gen-ghost-track.py langhorne-speedway \
        --prompt "Documentary-style vintage photo, one continuous mile of dirt..."

Generate, label, AND wire it into the register + rebuild:

    python3 scripts/gen-ghost-track.py columbia-speedway \
        --prompt "..." --caption "Too Fast to Handle, Imagined" --deploy

Let the prompt be built from the register entry (surface guessed from the body):

    python3 scripts/gen-ghost-track.py linden-airport --deploy

Pick the engine or model, or list what your key can see:

    python3 scripts/gen-ghost-track.py <slug> --engine gemini
    python3 scripts/gen-ghost-track.py <slug> --model imagen-3.0-generate-002
    python3 scripts/gen-ghost-track.py --list-models

Nothing here commits or pushes. Review `git diff`, then deploy the site the
way you always do.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ghost-tracks.json")
IMAGES = os.path.join(ROOT, "images")
STAGING = os.path.join(IMAGES, "_staging")
LABELER = os.path.join(ROOT, "scripts", "label-imagined.py")

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
# Model IDs drift. These are sane defaults; if your key 403s on one, run
# --list-models and pass --model with one that's available to you.
DEFAULT_IMAGEN_MODEL = "imagen-3.0-generate-002"   # dedicated image model, :predict
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"    # native image gen, :generateContent

# The house wrapper. Every lesson from the slop audit lives here: keep the crowd
# distant and soft so no faces or hands mangle, and keep all text out of frame
# because no model renders signage reliably.
HOUSE_SUFFIX = (
    " Shot trackside on a 35mm lens, Kodak Portra color, heavy film grain, "
    "slight motion blur on the wheels, warm overcast-to-golden light. "
    "Charcoal, rust, cream and navy tones. The crowd is distant and soft in "
    "the haze. No readable text, no banners, no legible car numbers, no "
    "close-up hands or faces. Horizontal, 16:9."
)


def get_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    keyfile = os.path.join(ROOT, "scripts", ".gemini_key")
    if os.path.isfile(keyfile):
        return open(keyfile).read().strip()
    sys.exit("No API key. Set GEMINI_API_KEY or write scripts/.gemini_key "
             "(get one at https://aistudio.google.com/apikey).")


def _post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit("API error %s:\n%s\n\nIf this is a model-access or 404 error, "
                 "run --list-models and pass --model." % (e.code, body[:1200]))
    except urllib.error.URLError as e:
        sys.exit("Could not reach the API (%s). Run this on a machine with open "
                 "network, not inside the cloud session." % e.reason)


def load_entry(slug):
    data = json.load(open(DATA))
    for e in data:
        if e["slug"] == slug:
            return e
    sys.exit("No entry with slug %r in data/ghost-tracks.json." % slug)


def build_prompt(entry):
    """A reasonable auto-prompt from the register entry. A hand-written
    --prompt almost always beats this; use it for anything you care about."""
    body = (entry.get("body") or "").lower()
    if "superspeedway" in body or "two-mile" in body or "2-mile" in body:
        surface = ("a wide, high-banked paved superspeedway, a pack of period "
                   "stock cars at speed low on the banking")
    elif "clay" in body:
        surface = ("a half-mile red-clay dirt oval, period stock cars sliding "
                   "through a turn kicking up deep red dust")
    elif "board" in body:
        surface = ("a steeply banked wooden board track, early stock or open-"
                   "wheel cars roaring along the planks")
    else:
        surface = ("a half-mile dirt oval, period stock cars sliding through a "
                   "dusty turn")
    era = entry.get("era", "")
    decade = "late-1950s"
    for d in ("1910s", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s"):
        if d[:3] in era:
            decade = "early-" + d
            break
    return ("Documentary-style vintage photograph, %s American stock car race on "
            "%s, a low wooden grandstand and the local landscape of %s behind."
            % (decade, surface, entry.get("place", "the American South"))
            ) + HOUSE_SUFFIX


def gen_imagen(prompt, key, model, aspect="16:9"):
    url = "%s/models/%s:predict?key=%s" % (API_BASE, model, key)
    out = _post(url, {"instances": [{"prompt": prompt}],
                      "parameters": {"sampleCount": 1, "aspectRatio": aspect}})
    preds = out.get("predictions") or []
    if not preds or "bytesBase64Encoded" not in preds[0]:
        sys.exit("Imagen returned no image. Raw: %s" % json.dumps(out)[:800])
    return base64.b64decode(preds[0]["bytesBase64Encoded"])


def gen_gemini(prompt, key, model):
    url = "%s/models/%s:generateContent?key=%s" % (API_BASE, model, key)
    out = _post(url, {"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"responseModalities": ["IMAGE"]}})
    for cand in out.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    sys.exit("Gemini returned no image. Raw: %s" % json.dumps(out)[:800])


def list_models(key):
    url = "%s/models?key=%s&pageSize=200" % (API_BASE, key)
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.load(r)
    for m in data.get("models", []):
        methods = ",".join(m.get("supportedGenerationMethods", []))
        if "image" in m["name"].lower() or "imagen" in m["name"].lower() \
                or "predict" in methods or "generateContent" in methods:
            print("%-45s %s" % (m["name"].replace("models/", ""), methods))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?", help="ghost-track slug, e.g. columbia-speedway")
    ap.add_argument("--prompt", help="hand-written prompt (house suffix appended)")
    ap.add_argument("--caption", help="plate-title caption, e.g. 'The Big Left Turn, Imagined'")
    ap.add_argument("--engine", choices=["imagen", "gemini"], default="imagen")
    ap.add_argument("--model", help="override the model id")
    ap.add_argument("--deploy", action="store_true",
                    help="also write image+imagined+caption to the entry and rebuild")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    key = get_key()
    if args.list_models:
        list_models(key)
        return
    if not args.slug:
        ap.error("slug is required (or use --list-models)")

    entry = load_entry(args.slug)
    prompt = (args.prompt + HOUSE_SUFFIX) if args.prompt else build_prompt(entry)
    print("Prompt:\n  " + prompt + "\n")

    model = args.model or (DEFAULT_GEMINI_MODEL if args.engine == "gemini"
                           else DEFAULT_IMAGEN_MODEL)
    print("Generating via %s (%s)..." % (args.engine, model))
    img = gen_imagen(prompt, key, model) if args.engine == "imagen" \
        else gen_gemini(prompt, key, model)

    # Searchable source name, kept out of the git-tracked images dir.
    os.makedirs(STAGING, exist_ok=True)
    source = os.path.join(STAGING, "%s-source.png" % args.slug)
    open(source, "wb").write(img)
    print("Saved source: %s (%d KB)" % (source, len(img) // 1024))

    # Burn the imagined label, natural name.
    out = os.path.join(IMAGES, "ghost-tracks-%s.jpg" % args.slug)
    subprocess.run([sys.executable, LABELER, source, out,
                    "--name", entry["name"], "--card"], check=True)

    if not args.deploy:
        print("\nDone (not deployed). Review the image, then re-run with "
              "--deploy and --caption to wire it in.")
        return

    caption = args.caption or ("%s, Imagined" % entry["name"])
    data = json.load(open(DATA))
    for e in data:
        if e["slug"] == args.slug:
            e["image"] = "/images/ghost-tracks-%s.jpg" % args.slug
            e["imagined"] = True
            e["caption"] = caption
            e.pop("alt", None)  # drop any stale ephemera alt (e.g. the old stub)
            break
    json.dump(data, open(DATA, "w"), indent=2, ensure_ascii=False)
    open(DATA, "a").write("\n")
    print("Wired into data/ghost-tracks.json (caption: %r)" % caption)

    subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                    "build-ghost-tracks.py")], check=True)
    print("\nBuilt. Review `git diff`, then commit and push the way you always do.")


if __name__ == "__main__":
    main()
