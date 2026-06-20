# jbrowse

`jbrowse` is a tiny terminal UI Jellyfin browser and `mpv` launcher.

It lets you log into Jellyfin, browse/search your media locally, open an info page, and launch playback in `mpv`.

Current prototype version:

```text
0.0.33
```

Current main script:

```text
jbrowse.py
```

## Status

This is an actively evolving prototype. It is usable, but not yet packaged.

Current features:

- Jellyfin login.
- Local browsing/search after item load.
- Fast list rendering using a single Textual `Static` widget.
- Title/filename display modes.
- Regex search using `/pattern`.
- Info page with Jellyfin-style media details.
- Jellyfin resume progress on the info page.
- Episode navigation from info page.
- Subtitle picker from the info page.
- Background `mpv` playback while `jbrowse` stays open.
- Minimal Jellyfin playback reporting for recently played state.
- Configurable `mpv_cmd` playback template.
- `mpv` command/output viewer with `Ctrl+G`.
- Resume start position from Jellyfin user data.
- Sort modes:
  - recently added
  - last played
  - premiere date
  - name
  - series order
- Sort mode and sort direction persistence.
- Theme cycling.
- Simple item cache for faster startup.
- Background Jellyfin refresh after cached startup.
- Non-blocking manual refresh with `Ctrl+R`.
- Periodic background refresh while recently active.
- Background refresh after playback returns.
- Example config and gitignore.
- Theme files under `themes/`, including Batman low/high contrast themes.

Not implemented yet:

- mpv IPC.
- Now Playing page.
- Accurate mpv IPC-backed Jellyfin playback progress reporting.
- Static bitrate/transcoding selection.

## Screenshots

These screenshots use the committed fictional fixture library, not a real Jellyfin server or media collection.

See [THEMES.md](THEMES.md) for the complete named-theme gallery.

### Browser

The main library view with the selected item highlighted.

![Browser screenshot](docs/screenshots/browser.svg)

### Theme Cycle

The browser after a `Ctrl+X` theme cycle.

![Theme cycle screenshot](docs/screenshots/after-ctrl-x.svg)

### Search

Typing `otter` filters the fixture library and shows the current match count.

![Search screenshot](docs/screenshots/search.svg)

### Item Information

Episode details, stream metadata, and the current subtitle choice.

![Item information screenshot](docs/screenshots/info.svg)

### Subtitle Picker

The per-item subtitle selector opened from the information panel.

![Subtitle picker screenshot](docs/screenshots/subtitles.svg)

### Help

The in-app keyboard reference.

![Help screenshot](docs/screenshots/help.svg)

### mpv Log

The captured mpv command and output view.

![mpv log screenshot](docs/screenshots/mpv-log.svg)

### Refresh State

The browser while a background refresh is in progress.

![Refresh state screenshot](docs/screenshots/refreshing.svg)

## Requirements

Python dependencies:

```bash
pip install textual requests
```

System dependency:

```bash
mpv
```

On Arch/CachyOS:

```bash
sudo pacman -S mpv python-requests python-textual
```

Depending on repo/package availability, `pip install textual requests` may be easier during development.

## Quick start

Put the script somewhere convenient:

```bash
chmod +x jbrowse.py
./jbrowse.py
```

Create a config file named:

```text
jbrowse.conf
```

Either next to the script or at:

```text
~/.config/jbrowse/jbrowse.conf
```

Example:

```ini
[jellyfin]
url = http://127.0.0.1:8096
username = your-login
password = your-password

[library]
types = Movie,Episode,Video,MusicVideo

[ui]
sort_mode = added
sort_desc = true
max_display_items = 0
display_mode = title

[style]
# path = themes/03-jbrowse-batman-low-contrast.tcss

[mpv]
# mpv_cmd = mpv --hwdec=auto --force-media-title="$filename" $subtitle $start "$url"

[cache]
refresh_interval_minutes = 10
```

## Config lookup

`jbrowse` looks for config in this order:

1. `jbrowse.conf` next to the script.
2. `~/.config/jbrowse/jbrowse.conf`.

If no config exists, it prints an example and exits.

## State file

`jbrowse` stores its Jellyfin device id in:

```text
jbrowse.state
```

Lookup order:

1. `jbrowse.state` next to the script, if it exists.
2. `~/.cache/jbrowse/jbrowse.state`.

The state format is:

```ini
[state]
deviceid =
```

## Item cache

`jbrowse` stores a simple item cache in:

```text
jbrowse.items.json
```

Lookup/write behavior:

1. Use `jbrowse.items.json` next to the script if it exists.
2. Otherwise use `~/.cache/jbrowse/jbrowse.items.json`.

The app still logs into Jellyfin on startup, but if the item cache exists it opens from cache first and starts a background refresh.

Manual refresh with `Ctrl+R` fetches a new item list in the background and writes the cache. Refresh status appears in the bottom status bar.

Periodic refresh is controlled by:

```ini
[cache]
refresh_interval_minutes = 10
```

`0` disables periodic refresh. Positive values refresh in the background only if `jbrowse` has been active in the last 10 minutes. Foreground `mpv` playback counts as inactive because the TUI is not running while playback owns the terminal.

## mpv command config

`jbrowse` launches playback with this built-in command template:

```text
mpv --hwdec=auto --force-media-title="$filename" $subtitle $start "$url"
```

You can override it in `jbrowse.conf`:

```ini
[mpv]
mpv_cmd = mpv --hwdec=auto --force-media-title="$filename" $subtitle $start "$url"
```

Supported placeholders:

```text
$url       Jellyfin stream URL, required
$filename  filename used for mpv's media title
$title     Jellyfin display title
$subtitle  --sid=no or --sid=N, omitted for auto subtitles
$start     --start=SECONDS, omitted when there is no resume position
```

`{url}` style placeholders also work. Commands are parsed with shell-like quoting, so quote paths or values that contain spaces.

## Server writes

Login, item fetching, screenshot harvesting, and stream URL construction do not write Jellyfin media state. The only intentional server mutations are the registered playback session reports: start, progress, and stopped. After playback returns, `jbrowse` refreshes in the background so local sort/cache data can pick up changed Jellyfin playback metadata. Future features that write additional Jellyfin state, such as manual watched-state changes, metadata edits, deletes, favorites, or played/unplayed toggles, should be documented and explicitly registered when they are added.

For local playback troubleshooting, each playback writes a timestamped `~/.cache/jbrowse/mpv.out-YYYYMMDD-HHMMSS-ffffff` file. It records the exact command, mpv output and exit code, plus whether each Jellyfin playback report was accepted or failed. These local logs can contain stream credentials; do not share them.

## Controls

### Browser

```text
Enter        show selected item info
Shift+Enter  play selected item immediately
Tab          next sort mode
Left/Right   previous/next sort mode while list is focused
Ctrl+O       toggle ascending/descending sort
Ctrl+T       toggle title/filename display and search
Up/Down      move selection; Up at top returns to search
PageUp/Down  move by a page
Home/End     jump to first/last shown result
Typing       from list: return to search and keep typed char
Esc          clear search
/pattern     regex search
Ctrl+R       refresh Jellyfin list in the background
Ctrl+G       show mpv output
Ctrl+K       stop active mpv playback
Ctrl+X       cycle theme and save it to jbrowse.conf
Ctrl+L       show help
F1 or ?      show help
Ctrl+C       quit (stops active mpv first)
```

### Info page

```text
q/backspace  close info
Enter        play shown item
s            open subtitle picker
Ctrl+R       refresh Jellyfin list in the background
←/→          previous/next episode
[/]          previous/next season
↑/↓          scroll
PgUp/PgDn    scroll by page
Home/End     top/bottom
```

### Subtitle picker

```text
↑/↓          select subtitle mode/track
Enter        apply
q/backspace  cancel
```

The info page's `Progress` field shows Jellyfin's saved resume position as `elapsed / runtime`. It updates after the post-playback background refresh completes. Subtitle choices are runtime-only for now. `auto` keeps mpv's default behavior, `none` disables subtitles, and a selected Jellyfin subtitle stream is passed to `mpv` as a best-effort track selection.

## Search

Normal search is case-insensitive substring search.

Regex search starts with `/`.

Examples:

```text
/Euphoria.*2160p
/S0[12]E0[1-9]
/Batman|Superman
/Heavy.*Head
```

Without the leading slash, regex characters are treated literally.

## Sort modes

Valid config values:

```text
added
played
premiere
name
series
```

Display labels:

```text
recently added
last played
premiere date
name
series order
```

`Ctrl+O` toggles descending/ascending.

The top bar shows arrows:

```text
↓ descending
↑ ascending
```

## Themes

A style can be selected with:

```bash
./jbrowse.py --style path/to/theme.tcss
```

Or in config:

```ini
[style]
path = themes/02-jbrowse-batman-high-contrast.tcss
```

Relative style paths are resolved relative to `jbrowse.conf`.

`Ctrl+X` cycles discovered `.tcss` files from `themes/`, the script directory, and `~/.config/jbrowse`, then saves the selected one.

The Batman themes are:

```text
themes/02-jbrowse-batman-high-contrast.tcss
themes/03-jbrowse-batman-low-contrast.tcss
```

Place them next to the script or under:

```text
~/.config/jbrowse/
```

## Gitignore

Do not commit local runtime files:

```text
jbrowse.conf
jbrowse.state
jbrowse.items.json
jbrowse.items.json.tmp
jbrowse.tcss
tools/screenshot/
```

Commit named themes under `themes/` instead.

## Development notes

The list renderer intentionally uses one `Static` widget instead of Textual `ListView`/`ListItem`. This is for speed with large libraries.

The current playback model starts `mpv` in the background while `jbrowse` stays open. Output is captured for the `Ctrl+G` log page.

Future work should add mpv IPC to the existing `PlaybackManager` for accurate progress, pause/seek controls, and track switching.

Experimental fixture UI screenshots:

```bash
python tools/svg_screenshot_poc.py
```

This writes local SVG screenshots under `tools/screenshot/` using committed fictional data from `tools/fake_cache_data.json` or, when present, `tools/fake_cache_data.json.zst`. The output is ignored by git so screenshots can be regenerated freely and only selected documentation images need to be added deliberately.

Feature a specific fictional item in the captures with a title, filename, or series substring:

```bash
python tools/svg_screenshot_poc.py --item "otter"
```

Generate the complete named-theme gallery only when it is explicitly needed:

```bash
python tools/svg_screenshot_poc.py --item "otter" --all-themes
```

This replaces the tracked SVGs under `docs/themes/`; it is intentionally not part of the routine release harness run.

Browse the same fixture data interactively without contacting Jellyfin or changing the real item cache/config:

```bash
./jbrowse.py --fake
```

To compress a large fixture file in place:

```bash
tools/compress_fake_cache.sh
```

Use your local cache and Jellyfin server only when explicitly wanted:

```bash
python tools/svg_screenshot_poc.py --real
```

Real-mode output can contain private media names and remains ignored by git.

Optional fake playback capture smoke test:

```bash
python tools/svg_screenshot_poc.py --playback-smoke
```

This uses a no-video fake player command that prints output every 0.5 seconds for about 3 seconds, then verifies the captured command/output path.
