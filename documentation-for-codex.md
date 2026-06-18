# documentation-for-codex.md

## Purpose of this document

This document is written for a future coding agent, especially Codex, so it can continue the `jbrowse` project without losing the decisions, constraints, and rationale from the ChatGPT prototyping session.

The current working script is:

```text
jbrowse_fresh_0_24.py
```

Current app version inside the script:

```text
0.24
```

The current stable baseline before the latest batch was:

```text
jbrowse_fresh_0_23.py
```

Version `0.24` adds sort modes, persisted sort state, a simple item cache, Batman themes, and a small page-state cleanup. It intentionally does **not** add mpv IPC, background mpv, Jellyfin playback reporting, subtitle picker, static bitrate/transcoding, or threaded refresh.

## High-level project goal

`jbrowse` is a small terminal UI launcher for Jellyfin media. It is designed to replace a shell/fish history style workflow where the user searched previously played Jellyfin media and launched it in `mpv`.

The user wants something that remains simple, fast, and practical:

- Use Jellyfin as the library source.
- Search and browse locally after initial item load.
- Play selected media in `mpv`.
- Prefer simple local config/state files.
- Avoid complex dependencies.
- Keep iteration speed high.
- Make the TUI feel fast even with thousands of items.
- Avoid over-engineering until needed.
- Preserve user state across playback.

The project is intentionally a single Python script right now. Splitting into modules is a future cleanup task, not an immediate priority.

## User environment and preferences

The user is on Arch/CachyOS Linux with GNOME/Wayland. Assume Linux. Do not write Windows/macOS instructions unless explicitly asked.

The user prefers:

- Practical code over theoretical explanation.
- Simple config files.
- Clear changelogs.
- `vim` in terminal examples, not `nano`.
- Unique generated filenames and SHA256 hashes when handing over new builds.
- Avoiding stale file confusion.
- Arch-style commands where packaging examples are needed.
- Not committing personal config/cache/state files.

## Current runtime dependencies

The script depends on:

```text
python
requests
textual
rich
mpv
```

Install Python dependencies with:

```bash
pip install textual requests
```

`rich` is normally installed by Textual, but the script imports it directly.

`mpv` must be available on `$PATH`.

## Current repo/runtime files

### Main script

```text
jbrowse_fresh_0_24.py
```

The current single-file app.

In a real repo this may eventually be renamed to:

```text
jbrowse
```

or:

```text
jbrowse.py
```

Do not do that rename casually while the user is still comparing generated files by version.

### Example config

```text
jbrowse_conf_example_0_24.conf
```

This is the current generated example config. In the repo it should probably be committed as:

```text
jbrowse.conf.example
```

Do **not** commit the real `jbrowse.conf`.

### Gitignore

```text
jbrowse_gitignore_0_24.txt
```

This should become `.gitignore` in the repo.

It ignores:

```text
jbrowse.conf
jbrowse.state
jbrowse.items.json
jbrowse.items.json.tmp
jbrowse.tcss
__pycache__/
*.py[cod]
```

### Themes

Current extra theme pack:

```text
jbrowse_batman_themes_0_24.zip
```

Contains:

```text
jbrowse-batman-low-contrast.tcss
jbrowse-batman-high-contrast.tcss
```

Earlier theme pack from the session:

```text
jbrowse_themes_0_15.zip
```

That older pack was built after the UI switched from `ListView`/`ListItem` to a single `Static` list renderer.

## Runtime file lookup rules

### Config file

The app always looks for a config named:

```text
jbrowse.conf
```

Lookup order:

1. `jbrowse.conf` next to the script/executable.
2. `~/.config/jbrowse/jbrowse.conf`.
3. If none exists, print a minimal example to stderr and exit.

The script should not auto-generate a real config file with secrets.

### State file

The state file is:

```text
jbrowse.state
```

Lookup order:

1. `jbrowse.state` next to the script, **if it exists**.
2. Otherwise `~/.cache/jbrowse/jbrowse.state`.

The state is INI format:

```ini
[state]
deviceid =
```

It stores the Jellyfin device id used in the authorization header. Do not revert to a separate `device-id` file.

### Item cache

Version `0.24` adds a simple item cache:

```text
jbrowse.items.json
```

Lookup/write path:

1. `jbrowse.items.json` next to the script, **if it already exists**.
2. Otherwise `~/.cache/jbrowse/jbrowse.items.json`.

The cache is intended to speed startup by avoiding a full Jellyfin item fetch on every launch.

The app still logs into Jellyfin on startup because playback URLs need a valid auth token. The slow part is fetching thousands of items, not the login.

The cache is display cache, not truth. If a cached item is stale, a manual refresh fixes it.

### Style file

Style lookup order:

1. `--style path`
2. `[style] path = ...` in `jbrowse.conf`
3. `jbrowse.tcss` next to the script, if it exists
4. `~/.config/jbrowse/jbrowse.tcss`, if it exists
5. built-in fallback CSS

Relative `[style] path` values are resolved relative to `jbrowse.conf`.

`Ctrl+X` cycles discovered `.tcss` files and persists the selected theme to `[style] path`.

## Current config format

Current example:

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

Valid `sort_mode` values:

```text
added
played
premiere
name
series
```

Meaning:

```text
added     = recently added
played    = last played
premiere  = premiere date
name      = name
series    = series order
```

`sort_desc = true` means descending/down arrow.

`max_display_items = 0` means unlimited.

`display_mode` is either:

```text
title
filename
```

## Current UI model

The UI is built with Textual.

Important: the list is **not** Textual `ListView` or `ListItem`. It is a single `Static` widget named `ItemPane` that renders only the current viewport as Rich `Text`.

This was a major performance decision. Do not reintroduce `ListView`/`ListItem` unless there is a very good reason and performance is tested.

The layout:

```text
top status bar
search input
single Static item pane
bottom status bar
```

Search, sort, and display mode are local after the item list is loaded. Typing in the search bar should not trigger Jellyfin calls.

Manual refresh is still blocking in 0.24. Background refresh is a planned future feature.

## Current page-state model

Version `0.24` introduces a small page-state cleanup. The app now treats the current screen as a named page instead of separate `help_visible` and `info_visible` booleans.

Current pages:

```text
browser
help
info
```

Future pages planned:

```text
now_playing
mpv_log
subtitle_picker
confirm_replace
```

Backspace behavior should remain predictable:

```text
browser: normal search/list behavior
info: return to browser
help: return to previous page
```

Important test:

1. Open an info page.
2. Press `F1`.
3. Press any key.
4. It should return to the info page, not the browser.

## Current keybindings

### Browser/list

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
↑/↓          scroll info
PgUp/PgDn    scroll by page
Home/End     top/bottom
```

## Important terminal key decision

`Ctrl+I` is **not** used for info anymore. In terminals, `Ctrl+I` is Tab. Earlier the user observed `Ctrl+I` toggling the view because it was indistinguishable from Tab. Do not restore `Ctrl+I` as an advertised hotkey.

`F2` was also rejected by the user. The current model is:

```text
Enter        open info
Shift+Enter  play directly
```

## Search behavior

Search is local against the current display text.

If display mode is `title`, search uses formatted Jellyfin titles.

If display mode is `filename`, search uses filenames/paths where available.

Plain search is case-insensitive substring search.

Regex search is triggered by a leading slash:

```text
/Euphoria.*2160p
```

Without the leading slash, `Euphoria.*2160p` is searched literally.

Regex examples to test:

```text
/Euphoria.*2160p
/S0[12]E0[1-9]
/Batman|Superman
/Heavy.*Head
```

Invalid regex should not crash. It should show a regex error in the top bar and return zero matches.

## Sort modes

Current sort modes:

```text
added
played
premiere
name
series
```

Top bar examples:

```text
sort: recently added ↓
sort: last played    ↓
sort: premiere date  ↓
sort: name           ↓
sort: series order   ↓
```

`played` sort includes all items, not only items with `LastPlayedDate`.

For `played`, played items sort first by last played date. Unplayed items appear after, with a date-created fallback.

`series` sort is intended primarily for episodes:

```text
SeriesName
SeasonNumber
EpisodeNumber
PremiereDate/DateCreated fallback
Title
```

Movies and non-episode videos use title/date fallback.

## Playback model in 0.24

Current playback is still foreground `mpv`.

The command shape is:

```bash
mpv --hwdec=auto --force-media-title="$filename" "$url"
```

If Jellyfin has a resume position, it appends:

```bash
--start=<seconds>
```

The `--force-media-title` value intentionally uses the filename, not the pretty Jellyfin title.

There is no mpv IPC yet.

There is no Jellyfin playback reporting yet.

There is no background mpv yet.

There is no now-playing page yet.

There is no static bitrate/transcoding yet.

## Current Jellyfin usage

The script logs in with:

```text
/Users/AuthenticateByName
```

It fetches items with:

```text
/Users/{user_id}/Items
```

It streams with:

```text
/Videos/{item_id}/stream?static=true&api_key=...
```

or for audio:

```text
/Audio/{item_id}/stream?static=true&api_key=...
```

The item fetch includes fields like:

```text
DateCreated
UserData
SeriesName
ParentIndexNumber
IndexNumber
ProductionYear
Path
MediaSources
Overview
Genres
OfficialRating
CommunityRating
PremiereDate
RunTimeTicks
ProviderIds
SortName
```

## Known deliberate non-features right now

Do not add these accidentally:

```text
mpv IPC
/Sessions/Playing reporting
static bitrate/transcoding
subtitle picker
background mpv
second terminal launch
threaded refresh
periodic refresh
refresh after playback
```

These are planned, but they should be implemented deliberately as separate passes.

## Banned/stale strings from previous iterations

When generating a new script, continue checking for these unless intentionally implementing one of them:

```text
CONFIG_PATH
config.ini
Created example config
[player]
mpv =
hwdec =
resume_min_remaining_seconds
report_progress
progress_interval_seconds
input-ipc-server
sock_path
/Sessions/Playing
CACHE_DIR
device_path
BINDINGS
ListView
ListItem
subprocess.run(args)
Ctrl+F
event.key == "ctrl+f"
Ctrl+I
event.key == "ctrl+i"
F2           show
event.key == "f2"
toggle played/added
```

Some of these will intentionally stop being banned later. For example:

- `input-ipc-server` will be needed when mpv IPC is implemented.
- `/Sessions/Playing` will be needed when Jellyfin playback reporting is implemented.
- `[player]` may be needed if playback configuration is added.

Until then, they are useful stale-regression checks.

## Current known files and hashes from handoff

These are the latest files produced in the session:

```text
jbrowse_fresh_0_24.py
SHA256: 9fb0b2bb450cba6dbefedeb9a39f465bbee126b15117bdabf7d826e308661add

jbrowse_batman_themes_0_24.zip
SHA256: 6fb227d31bc422961fb55407a003b942b63e0da70d5a162cd2ca59ba7bdb4f02

jbrowse_conf_example_0_24.conf
SHA256: e9e7300dafab7e3ac56a2020bde8f2616317392b9ddafc41fc9faad3e3d21127

jbrowse_gitignore_0_24.txt
SHA256: b3fc99a8a5f8924960a4fd22eb06ef5e198c6ba53e9458ad5cdfe5c061ed9b3d
```

## Testing checklist for the next agent

After touching code, run:

```bash
python -m py_compile jbrowse_fresh_0_XX.py
```

Then run a stale-string check for the banned strings above.

Then manual runtime tests:

1. Fresh config error prints a useful example.
2. Config loads from script directory.
3. State loads/saves from expected path.
4. First launch fetches Jellyfin and writes `jbrowse.items.json`.
5. Second launch loads cache.
6. `Ctrl+R` refreshes and updates cache.
7. Tab cycles all five sort modes.
8. Left/right cycles sort modes while list is focused.
9. Ctrl+O toggles arrow direction and persists `sort_desc`.
10. Sort mode persists to config.
11. Search works in title mode.
12. Search works in filename mode.
13. Regex examples work.
14. Invalid regex shows error instead of crashing.
15. Enter opens info.
16. Shift+Enter plays.
17. Info episode navigation works.
18. Help returns to info if opened from info.
19. Ctrl+X cycles themes and persists style.
20. Batman themes are discoverable when placed in the theme search path.

## Future architecture advice

The next major architectural boundary should be a `PlaybackManager` object.

It should eventually own:

```text
mpv process
mpv IPC socket
mpv stdout/stderr rolling log
current item
time-pos
duration
pause state
quality setting
subtitle/audio selection
Jellyfin reporting state
```

Do not cram this into random UI methods. Keep UI as a consumer of player state.

For now, 0.24 intentionally avoids that.
