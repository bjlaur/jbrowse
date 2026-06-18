# changelog.md

This changelog summarizes the ChatGPT prototyping session that produced the current `jbrowse` prototype.

The current generated script is:

```text
jbrowse_fresh_0_24.py
```

Current app version:

```text
0.24
```

## Project origin

The project started as a replacement for a shell/fish workflow around Jellyfin history and `mpv` playback.

The original idea was roughly:

- Search Jellyfin items.
- Pick something from history/search.
- Launch it in `mpv`.

It grew into a Textual TUI browser with sorting, search, info pages, themes, and a simple cache.

## Major design decisions

### Keep the app as a single Python script for now

The app is currently one file for fast iteration. Splitting into modules is planned later.

### Use Textual

Textual provides the TUI layout, input handling, and widgets.

### Do not use Textual ListView/ListItem

The first list implementation was too heavy for thousands of media items. The list was changed to a single custom `Static` widget (`ItemPane`) that renders only visible rows.

This is a major performance decision and should not be casually undone.

### Config file is always `jbrowse.conf`

The app looks next to the script and then in `~/.config/jbrowse/`.

### State file is `jbrowse.state`

This stores Jellyfin DeviceId in INI format.

### No `[player]` config yet

The user explicitly wanted no player config while playback is simple. `mpv` and `--hwdec=auto` are hardcoded for now.

### `Ctrl+I` was rejected

In terminals, `Ctrl+I` is Tab. It caused the info hotkey to toggle sort/view behavior. Info is now opened with `Enter`.

### `F2` was rejected

F2 worked technically, but the user disliked it. Current behavior:

```text
Enter        open info
Shift+Enter  play directly
```

## Version history

### 0.9 era

A stable early version was produced and hash-checked. The user became concerned about stale files, so later handoffs used unique filenames and SHA256 hashes.

Important practice established:

- Use unique generated filenames.
- Include SHA256.
- Run syntax checks.
- Run stale/banned-string checks.

### 0.10

Focused on initial list performance and interaction polish.

Key work:

- Optimized initial list cap behavior.
- Improved Tab/search focus behavior.

### 0.11

Key work:

- `Ctrl+C` quits TUI.
- Config parser uses `strict=False` so duplicate keys while editing do not immediately break config parsing.

### 0.12 / 0.13

UI layout work.

Key work:

- Top/bottom status experimentation.
- Search bar set to height 1.
- Added style file lookup.
- Introduced `jbrowse.tcss`.

### 0.14

Theme cycling.

Key work:

- Added `[style] path`.
- Added `Ctrl+X` to cycle discovered `.tcss` files.
- Persist selected theme to config.
- Added bottom status bar.
- Produced theme pack.

### 0.15

Major list performance improvement.

Key work:

- Replaced Textual `ListView`/`ListItem` with single `Static` widget.
- Manual selection and scrolling.
- List renders only the visible viewport.
- Theme CSS updated for `#items`.

This is one of the most important implementation milestones.

### 0.16

Refresh and help work.

Key work:

- `max_display_items = 0` means unlimited.
- `Ctrl+C` while mpv is running terminates mpv and returns cleanly.
- Theme switch rendering improved.
- Removed automatic refresh after mpv.
- Added manual `Ctrl+R` refresh.
- Added help overlay.

### 0.17

Theme persistence.

Key work:

- `Ctrl+X` selected theme persists to `[style] path` in active `jbrowse.conf`.

### 0.18

Filename/title display mode.

Key work:

- mpv title uses filename instead of pretty Jellyfin title.
- Fetches Jellyfin `Path`/`MediaSources` and stores best-effort filename.
- Added display/search mode toggle.
- Display mode persists to `[ui] display_mode`.
- Search uses the current display text.
- Top bar simplified.
- Refresh shown inside TUI instead of dumping to a black screen.

### 0.19

Info hotkey and help overlay changes.

Key work:

- Replaced `Ctrl+F` display toggle with `Ctrl+T`.
- Added centered floating help panel.
- Added centered refresh panel.
- Added refresh failure panel.

### 0.20

Sort labels and initial info overlay.

Key work:

- Top bar labels became:
  - `sort: last played`
  - `sort: recently added`
- `played` sort changed to include **all** items, not only items with `LastPlayedDate`.
- Unplayed items go after played items.
- Added `Ctrl+O` sort direction toggle.
- Added initial `Ctrl+I` info overlay.
- Help key moved away from `Ctrl+H` because terminals often treat it as Backspace.

### 0.21

Jellyfin-like info overlay.

Key work:

- Redesigned info overlay to look more like Jellyfin details.
- Added video/audio/subtitle summary.
- Added synopsis, IDs, genres, technical details.
- Added scrollable info overlay.
- Added `q` to close info.
- Top bar advertises `F1 help`.
- Removed Backspace help line.

Current issue discovered after this:

- `Ctrl+I` behaved like Tab in terminal, so it toggled sort/view instead of opening info.

### 0.22

Info moved away from `Ctrl+I`.

Key work:

- Info opened with `F2`.
- Added episode navigation inside info:
  - left/right previous/next episode
  - `[` and `]` previous/next season
  - Enter plays shown episode
- Sort label changed to fixed-width-ish:
  - `sort: last played    ↓`
  - `sort: recently added ↓`
- Replaced `(desc)`/`(asc)` with arrows.
- Default initial view became recently added.

User then rejected F2 as the desired long-term info key.

### 0.23

Current stable pre-0.24 baseline.

Key work:

- `Enter` on list opens info.
- `Shift+Enter` plays immediately.
- `F2` removed from help/code.
- Info instructions moved to the top:
  - `q/backspace close | Enter play | ←/→ episode | [/] season | ↑/↓ scroll`
- Backspace closes info and returns to search/list UI.
- UI state survives mpv:
  - sort tab
  - sort direction
  - search text
  - selected item
  - list scroll
  - display mode
  - info page state
  - info item
  - info scroll
- Theme cycling preserves UI state.

0.23 is the safe rollback point if 0.24 has problems.

### 0.24

Latest generated version.

Key work:

#### Full sort modes

Added five sort modes:

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

Controls:

```text
Tab          next sort mode
Left/Right   previous/next sort mode while list focused
Ctrl+O       toggle asc/desc
```

#### Persist sort mode/order

Config now supports:

```ini
[ui]
sort_mode = added
sort_desc = true
```

`sort_mode` and `sort_desc` are written back when changed.

#### Simple item cache

Added:

```text
jbrowse.items.json
```

Startup:

- Log into Jellyfin.
- Try loading cached items.
- If no cache, fetch from Jellyfin and write cache.

Manual refresh:

- Fetch from Jellyfin.
- Write item cache.
- Update UI.

This is deliberately **not** background refresh.

#### Page-state cleanup

Replaced separate help/info booleans with named page state:

```text
browser
help
info
```

This is groundwork for future pages:

```text
now_playing
mpv_log
subtitle_picker
confirm_replace
```

#### Batman themes

Generated:

```text
jbrowse-batman-low-contrast.tcss
jbrowse-batman-high-contrast.tcss
```

Packaged as:

```text
jbrowse_batman_themes_0_24.zip
```

#### Regex test reminder

No major regex code change was requested. A smoke check confirmed that a regex like this compiles and matches in principle:

```text
/Euphoria.*2160p
```

Manual runtime testing is still needed.

## Generated support files

### `jbrowse_conf_example_0_24.conf`

Example config generated for the current config format.

### `jbrowse_gitignore_0_24.txt`

Gitignore for local runtime files.

### `documentation-for-codex.md`

This detailed handoff document.

### `README.me`

General user manual.

### `plan-document.md`

Future plan and sequencing.

## Known future features not yet implemented

- Subtitle picker.
- Passing selected subtitle to mpv.
- Background mpv process.
- mpv stdout/stderr capture.
- mpv output/log panel.
- mpv IPC.
- Now Playing page.
- Replace playback confirmation dialog.
- `mpv loadfile` replacement.
- Jellyfin `/Sessions/Playing` start/progress/stopped reporting.
- Static bitrate/transcode selection.
- Restart-at-current-position to change bitrate.
- Threaded/non-blocking refresh.
- Periodic refresh.
- Refresh after playback.
- Split into modules.
- Rename script to final stable executable name.

## Regression risks to watch

### Cache staleness

A cached item may be deleted or renamed on Jellyfin. Refresh should fix this.

### Series sort

Series sort is meaningful for episodes, but movies and miscellaneous videos need sane fallback.

### Terminal key behavior

Do not assume all terminals send distinct keys for modified Enter/Space/etc. `Ctrl+I` already failed because it is Tab.

### Textual API differences

Textual changes over time. Prefer simple APIs and test on the user's installed version.

### Performance

Do not reintroduce a widget per media item. Keep the single `Static` viewport renderer unless there is a tested replacement.

## File hash record

Latest known generated files:

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
