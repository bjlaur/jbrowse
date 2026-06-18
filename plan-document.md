# plan-document.md

## Purpose

This is the working plan for `jbrowse`.

The project should evolve in small, testable steps. The current script is useful and should not be destabilized by bundling too many architectural changes at once.

The most important rule: separate small UI/config/cache work from the larger playback architecture work.

## Current baseline

Current generated version:

```text
jbrowse_fresh_0_24.py
```

Safe rollback baseline:

```text
jbrowse_fresh_0_23.py
```

0.23 is known to feel good. 0.24 adds useful small/medium improvements but should be tested carefully.

## Guiding principles

1. Keep startup fast.
2. Keep search and sort local.
3. Keep the UI responsive.
4. Keep playback reliable.
5. Do not make terminal key assumptions without testing.
6. Avoid over-engineering until the feature needs it.
7. Preserve user state whenever possible.
8. Prefer explicit config/state/cache files over hidden magic.
9. Do not reintroduce slow per-row widgets.
10. Use clear changelogs and SHA256 hashes for every generated handoff.

## Phase 1: stabilize 0.24

Goal: prove current changes work.

Test:

- Config loads.
- State loads.
- First run fetches items and writes cache.
- Second run loads cache.
- Ctrl+R refreshes and rewrites cache.
- All five sort modes work.
- Sort mode/order persists to config.
- Regex search works.
- Info page still works.
- Help opened from info returns to info.
- Batman themes load and cycle.

Fix only regressions. Do not add new features in this phase.

## Phase 2: subtitle picker

Goal: select subtitles in `jbrowse` before playback.

Scope:

- Add subtitle metadata to `MediaItem`.
- Add a subtitle picker from the info page.
- Picker options:
  - auto
  - none
  - each subtitle stream
- Store selected subtitle per item in runtime UI state.
- On playback, pass an mpv subtitle selection option where possible.

Possible UI:

```text
s            open subtitle picker from info
↑/↓          select
Enter        apply
q/backspace  cancel
```

Caveat:

Jellyfin stream indexes and mpv subtitle track ids may not always match. Pre-IPC subtitle selection may be approximate. The robust version requires mpv `track-list` over IPC.

## Phase 3: threaded refresh

Goal: make `Ctrl+R` not freeze the UI.

Scope:

- Background thread fetches Jellyfin items.
- UI shows refreshing state.
- Fetch completion updates:
  - in-memory items
  - item cache
  - current selected item if still present
- Refresh failures show error but preserve old items.

Do not add periodic refresh until manual background refresh is solid.

## Phase 4: periodic refresh and refresh-after-playback

Goal: keep cache fresh without annoying blocking.

Config:

```ini
[cache]
refresh_on_start = true
refresh_after_playback = true
refresh_interval_minutes = 0
```

`0` means disabled.

Scope:

- Startup may load cache immediately and refresh in background.
- Playback stop may trigger background refresh.
- Optional periodic refresh while UI is open.

This should happen after threaded refresh exists.

## Phase 5: PlaybackManager

Goal: stop treating playback as a simple blocking `subprocess.Popen(...).wait()` call.

Create a `PlaybackManager` object.

It should own:

```text
mpv process
mpv IPC socket path
mpv stdout/stderr log buffer
currently playing item
position
duration
pause state
quality
selected audio/subtitle
Jellyfin reporting status
```

Do not cram this into `BrowseApp`.

The UI should ask the PlaybackManager for current state and issue commands to it.

## Phase 6: background mpv and mpv log page

Goal: keep `jbrowse` open while mpv plays.

Implementation idea:

```python
subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    text=True,
    bufsize=1,
)
```

Read output in a background thread into:

```text
collections.deque(maxlen=2000)
```

Also optionally tee to:

```text
~/.cache/jbrowse/mpv.log
```

UI:

```text
Ctrl+G = mpv output/log page
```

The log page should support scroll, page up/down, end latest, and backspace close.

## Phase 7: mpv IPC

Goal: control and observe playback.

Launch mpv with:

```text
--input-ipc-server=<socket>
```

Needed commands/properties:

```text
get_property time-pos
get_property duration
get_property pause
get_property track-list
cycle pause
quit
seek
loadfile NEW_URL replace
set_property sid
set_property aid
```

This phase unlocks:

- Now Playing page.
- Pause/stop controls.
- Better subtitle/audio switching.
- Jellyfin progress reporting.
- Replace-current-playback flow.
- Static bitrate restart-at-current-position.

## Phase 8: Now Playing page

Goal: a live info page for the currently playing item.

The Now Playing page should be the info page plus live playback state, not a separate minimal page.

Sketch:

```text
Now Playing 8/10
q/backspace browser | Enter replace/play | Space pause | s subtitles
←/→ episode | [/] season | ↑/↓ scroll | Ctrl+G mpv log

FROM
Season 4 - 8. Heavy Is the Head

████████████░░░░░░░░░░░░░░  12:43 / 58:00
state: playing    quality: direct    subtitle: English - SUBRIP

Video       4K HEVC SDR
Audio       English - Dolby Digital+ - 5.1 - Default
Subtitles   English - SUBRIP

Synopsis...
Technical details...
```

Hotkey:

```text
Ctrl+N = open Now Playing
```

Backspace from Now Playing returns to browser, playback continues.

## Phase 9: replace playback dialog

Goal: if something is already playing and user starts another item, ask first.

Dialog:

```text
Replace playback?

Currently playing:
Heavy Is the Head

Replace with:
Next Episode?

y replace | n cancel
```

Possible implementation:

```text
mpv loadfile NEW_URL replace
```

If Jellyfin reporting gets complicated, stop/relaunch mpv instead.

## Phase 10: Jellyfin playback reporting

Goal: make Jellyfin resume/progress accurate.

Use mpv IPC position.

Endpoints to implement deliberately:

```text
/Sessions/Playing
/Sessions/Playing/Progress
/Sessions/Playing/Stopped
```

Report:

```text
ItemId
MediaSourceId when known
PositionTicks
CanSeek
IsPaused
```

Call `/Stopped` when mpv exits or item is replaced.

Do not implement this before mpv IPC. Without IPC, final position is guesswork.

## Phase 11: static bitrate/transcoding

Goal: choose a quality before playback.

Options:

```text
direct
40 Mbps
20 Mbps
12 Mbps
8 Mbps
4 Mbps
2 Mbps
```

Hotkey idea:

```text
Ctrl+B = cycle quality
```

Bottom bar:

```text
quality: direct
```

Static bitrate probably requires different Jellyfin stream/transcode URL parameters. This should be tested against the user's actual server.

## Phase 12: change bitrate while playing

Goal: approximate dynamic bitrate.

Not truly seamless.

Flow:

1. Get current `time-pos` from mpv IPC.
2. Stop or replace current stream.
3. Build new URL with new bitrate.
4. Start at previous position.

This is good enough for a first version.

## Phase 13: audio track picker

After subtitle picker and mpv IPC are working, add audio picker.

Controls may mirror subtitle picker:

```text
a = audio picker
s = subtitle picker
```

## Phase 14: split into modules

Only after the app stabilizes.

Possible layout:

```text
jbrowse/
  __init__.py
  __main__.py
  config.py
  cache.py
  jellyfin.py
  models.py
  player.py
  ui.py
  themes.py
```

Do not split too early. The single-file script has made fast iteration easier.

## Phase 15: packaging

Possible future packaging:

- executable script `jbrowse`
- `pyproject.toml`
- optional Arch PKGBUILD
- install example config to docs
- install themes to share directory or document copying them

## Near-term recommended next coding task

After testing 0.24, the next best coding task is likely:

```text
subtitle picker skeleton
```

or:

```text
threaded refresh
```

If 0.24 cache startup is enough, do subtitle picker first.

If startup/refresh still feels annoying, do threaded refresh first.

## Things to avoid next

Avoid bundling these together in one pass:

```text
threaded refresh
mpv IPC
Jellyfin reporting
subtitle picker
now playing page
transcoding
```

Each touches enough code to deserve its own testable version.

## Manual test list before any big rewrite

1. Run from cold config.
2. Run with existing config.
3. Run with existing cache.
4. Run after deleting cache.
5. Search title.
6. Search filename.
7. Regex search.
8. Invalid regex.
9. Sort all modes.
10. Sort asc/desc.
11. Persist sort config.
12. Info page.
13. Episode navigation.
14. Theme cycling.
15. mpv playback.
16. Ctrl+C during mpv.
17. Refresh.
18. Cache write.
