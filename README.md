# jbrowse

`jbrowse` is a tiny terminal UI Jellyfin browser and `mpv` launcher.

It lets you log into Jellyfin, browse/search your media locally, open an info page, and launch playback in `mpv`.

Current prototype version:

```text
0.24
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
- Episode navigation from info page.
- `mpv` playback.
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
- Example config and gitignore.
- Batman low/high contrast theme pack.

Not implemented yet:

- mpv IPC.
- Background mpv while keeping the UI open.
- Now Playing page.
- Jellyfin playback progress reporting.
- Static bitrate/transcoding selection.
- Subtitle picker.
- Threaded/non-blocking refresh.
- Periodic refresh.

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
username = bryan
password = your-password

[library]
types = Movie,Episode,Video,MusicVideo

[ui]
sort_mode = added
sort_desc = true
max_display_items = 300
display_mode = title

[style]
# path = jbrowse.tcss
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

The app still logs into Jellyfin on startup, but if the item cache exists it avoids a full library fetch.

Manual refresh with `Ctrl+R` fetches a new item list and writes the cache.

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
Ctrl+R       refresh Jellyfin list
Ctrl+X       cycle theme and save it to jbrowse.conf
Ctrl+L       show help
F1 or ?      show help
Ctrl+C       quit
```

### Info page

```text
q/backspace  close info
Enter        play shown item
←/→          previous/next episode
[/]          previous/next season
↑/↓          scroll
PgUp/PgDn    scroll by page
Home/End     top/bottom
```

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
path = jbrowse-batman-high-contrast.tcss
```

Relative style paths are resolved relative to `jbrowse.conf`.

`Ctrl+X` cycles discovered `.tcss` files and saves the selected one.

The Batman theme pack contains:

```text
jbrowse-batman-low-contrast.tcss
jbrowse-batman-high-contrast.tcss
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
```

Commit examples/themes instead.

## Development notes

The list renderer intentionally uses one `Static` widget instead of Textual `ListView`/`ListItem`. This is for speed with large libraries.

The current playback model is foreground `mpv`; when `mpv` exits, the UI returns.

Future work should add a real `PlaybackManager` with mpv IPC instead of bolting player logic onto UI methods.
