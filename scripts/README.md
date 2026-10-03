# Gemini frame ingest

Zero-touch ingest for T&R image frames. When a `Gemini_Generated_Image_*.png`
lands in `~/Downloads`, it gets converted to a web JPG and staged in
`images/_staging/` for naming and review. The raw PNG is moved to
`~/Downloads/_gemini_raw/`.

## What it does / doesn't

Does: watch Downloads, convert PNG to JPG (via built-in `sips`), stage, archive raw.

Doesn't: pick the frame, rename to a slug, move into `images/`, or commit.
Those stay manual on purpose — frame selection, naming, and the canon check
(right character, no readable labels, foothills not peaks) are human calls.

## Install (one time)

    cp ~/Documents/GitHub/throttle-and-rust-site/scripts/net.katadhin.tr-gemini-ingest.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/net.katadhin.tr-gemini-ingest.plist

The watcher now runs in the background and survives reboots.

## Test it

    bash ~/Documents/GitHub/throttle-and-rust-site/scripts/gemini-ingest.sh
    ls ~/Documents/GitHub/throttle-and-rust-site/images/_staging/

## Finish a frame (the manual half)

Pick the staged frame you want, then either rename it yourself or tell Claude
"file the latest staged frame as <slug>" and it becomes `images/<slug>-hero.jpg`.

## Uninstall

    launchctl unload ~/Library/LaunchAgents/net.katadhin.tr-gemini-ingest.plist
    rm ~/Library/LaunchAgents/net.katadhin.tr-gemini-ingest.plist

## Notes

- `WatchPaths` fires on any change to Downloads; the script filters to Gemini
  PNGs and exits fast otherwise, so the overhead is negligible.
- Files still downloading (`.crdownload`) or written in the last 2 seconds are
  skipped so a half-written frame never gets processed.
- Logs: `scripts/gemini-ingest.log` (staged frames), plus `.out.log` / `.err.log`.

---

# Videos page (`/videos/`)

`update-videos.py` keeps `/videos/` in step with the YouTube channel. It merges the
channel feed (newest 15 uploads) into `data/videos.json`, which keeps every video
ever seen, then renders `videos/index.html` from `videos-template.html`.

- Runs daily at 7:15am Eastern via `.github/workflows/videos.yml`, which commits
  any change and triggers the Pages deploy. Run it by hand from the repo's
  Actions tab ("Refresh videos page" → Run workflow) or locally with
  `python3 scripts/update-videos.py`.
- Edit the page through `videos-template.html`, never `videos/index.html`, which
  is overwritten on every run. `--render` re-renders without touching the feed.
- Anything 5 minutes or longer is filed under Full episodes; shorter is a clip.
  The newest full episode is the featured video.
- To drop a video from the page, delete its entry from `data/videos.json` and
  re-render. It will not come back unless it is re-uploaded.
