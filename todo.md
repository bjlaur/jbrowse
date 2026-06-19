# todo.md

## jbrowse TODO list, post-0.0.25

This file is intended for Codex or another coding agent continuing the `jbrowse` project.

Completed release work stays in this file as checked/crossed-out items so the roadmap keeps its history.

The current baseline already has:

- full sort modes
- persisted `sort_mode` / `sort_desc`
- regex search support
- Batman themes
- basic named page state for `browser`, `help`, and `info`
- simple `jbrowse.items.json` cache
- subtitle picker from the info page
- current config/example/gitignore/docs

Use this file as the roadmap and release-history checklist.

---

## Ground rules

- Keep `jbrowse.py` as the active single-file app until splitting it is clearly worth it.
- Keep the fast single-`Static` item renderer; do not return to Textual `ListView` / `ListItem` media rows.
- Keep phases separate. Do not bundle subtitle selection, threaded refresh, player IPC, Now Playing, and Jellyfin progress reporting into one large change.
- Do not add player config, mpv IPC launch options, or Jellyfin playback-reporting calls until the corresponding roadmap section is being implemented.
- Keep completed todo items marked as done instead of deleting them.
- Add a small `CHANGELOG.md` entry with a tiny testing summary after each release.
- Preserve current key decisions:

```text
Enter        info
Shift+Enter  direct playback
```

- Avoid `Ctrl+I` for info because terminals treat it as Tab.
- Avoid F2 for info; it was already rejected.

---

## Completed

- [x] ~~Subtitle selection from info screen.~~ Released in `0.0.25`.
- [x] ~~Create `CHANGELOG.md` with compact release notes and testing summaries.~~ Released in `0.0.25`.

---

## 1. Real-server UI screenshot POC

Goal: use the normal `jbrowse.conf` and real Jellyfin server to harvest a few UI screenshots for learning/review.

Output:

```text
screenshot/browser.svg
screenshot/info.svg
screenshot/subtitles.svg
screenshot/help.svg
```

Implementation notes:

- Keep this as a proof of concept, not a full test framework.
- Use the real server and normal config/cache flow.
- Do not launch `mpv`.
- Do not add pytest or a fake Jellyfin server yet.
- Keep `screenshot/` ignored because it can contain private media names.
- Theme cycling works in the POC and SVG titles include the theme name, but Textual's SVG renderer may flatten visual differences between dark themes.
- Later, compare Textual SVG export against a real terminal screenshot/capture if theme contrast matters for docs.

Manual release check:

- Run `python tools/ui_screenshot_poc.py`.
- Confirm the SVG files are created under `screenshot/`.
- Open at least one screenshot and confirm it looks like the real TUI.
- Confirm screenshots use different themes without changing `jbrowse.conf`.
- Confirm the SVG title shows the intended theme even if the rendered colors look too similar.

---

## 2. Server-side safety guard

Goal: keep track of code paths that can mutate Jellyfin/server state before we add playback reporting or other write APIs.

Current expectation:

- Login, fetch, stream URL construction, cache writes, and screenshot harvesting should not modify media metadata or playback state on the Jellyfin server.
- Future watched-state updates, playback progress reporting, metadata edits, deletes, favorites, and played/unplayed toggles should be treated as server-side mutations.

Implementation notes:

- Keep mutation-capable features behind explicit config/checks.
- Document mutation-capable endpoints before adding them.
- Keep this separate from the screenshot POC.

---

## 3. Better help text / key map cleanup

Goal: keep help readable as controls grow.

Suggested help sections:

```text
Browsing
Search
Info
Playback
Themes
App
```

This becomes more important once subtitles, now playing, mpv log, and quality controls exist.

Current help is acceptable, but every new feature should update the help page intentionally.

---

## 4. Configurable mpv command by format

Goal: allow practical per-format mpv launch command tuning from `jbrowse.conf`.

Examples of useful format buckets:

```text
default
hevc
h264
av1
mpeg2
hdr
4k
```

Possible behavior:

- Keep the current built-in `mpv` command as the default.
- Detect a simple format bucket from Jellyfin media stream metadata.
- Build the launch command from configured `mpv_cmd` values.
- Let config include the executable name as well as arguments, in case `mpv`, `mpvpaper`, a wrapper script, or a future custom launcher is useful.
- Keep matching conservative and predictable; codec-based matching is a good first version.
- Allow a default `mpv_cmd` plus format-specific overrides.

Useful examples this could support:

```text
default: mpv --hwdec=auto
hevc: mpv --hwdec=auto-safe --profile=gpu-hq
hdr: mpv --hwdec=auto --target-colorspace-hint=yes
```

Implementation notes:

- This can happen before `PlaybackManager` if it stays limited to building the launch command.
- Do not add mpv IPC as part of this task.
- Do not add background playback as part of this task.
- Update `jbrowse.conf.example` and README when the config shape is chosen.
- Be careful with quoting/splitting configured commands; use a structured or shell-safe parser rather than fragile string splitting.

---

## 5. Build files and Arch packaging skeleton

Goal: add the boring-but-useful project files that make `jbrowse` easier to install, build, and package.

Likely files:

```text
pyproject.toml
PKGBUILD
```

Possibly useful later:

- LICENSE
- ~~CHANGELOG.md~~
- Makefile
- install script
- desktop file
- man page
- shell completion

Implementation notes:

- Keep this lightweight; do not turn the project into a package migration unless needed.
- Preserve the single-file app shape unless a packaging tool truly requires a different layout.
- Prefer an Arch-friendly flow, since the target environment is Arch/CachyOS.
- Make sure local runtime files and private Jellyfin data stay out of packages.
- Update README with install/build notes once the files exist.

---

## 6. Non-blocking refresh

Current behavior:

```text
Ctrl+R blocks while Jellyfin fetch runs
```

Future behavior:

```text
Ctrl+R
UI stays responsive
top bar says refreshing...
background fetch runs
cache updates
list updates when done
```

Preserve during refresh:

```text
search text
selected item
scroll position
info item if still present
display mode
sort mode
sort direction
```

Implementation suggestion:

- Start with a background thread and a small queue.
- Worker thread fetches Jellyfin items.
- UI timer polls the queue.
- On success:
  - replace in-memory items
  - rebuild sorted views
  - write `jbrowse.items.json`
  - keep current selection if possible
- On failure:
  - keep old item list
  - show refresh error in status/help-style panel

Do not add periodic refresh until manual non-blocking refresh is solid.

---

## 7. Periodic refresh

After non-blocking refresh exists, consider config:

```ini
[cache]
refresh_interval_minutes = 30
```

Meaning:

```text
0 = disabled
positive number = refresh every N minutes while jbrowse is open
```

Requirements:

- Must not interrupt search/list/info usage.
- Must not steal focus.
- Must not block UI.
- Should update cache after a successful refresh.

---

## 8. Refresh after playback stops

After refresh is backgrounded, consider config:

```ini
[cache]
refresh_after_playback = true
```

Goal:

- After mpv exits, refresh watched/resume state.
- Do it in the background so returning from playback is not annoying.

This should wait until non-blocking refresh is implemented.

---

## 9. PlaybackManager

Big architecture piece.

Create a `PlaybackManager` object instead of having UI code directly own future playback state.

It should eventually own:

```text
mpv process
mpv IPC socket
mpv stdout/stderr log buffer
current item
position
duration
pause state
quality
subtitle/audio selection
Jellyfin reporting state
```

Responsibilities:

- Start playback.
- Stop playback.
- Replace playback.
- Track whether something is currently playing.
- Read mpv output.
- Later, send/receive mpv IPC commands.
- Later, report to Jellyfin.

Important guidance:

Do not cram all player logic into `BrowseApp`. `BrowseApp` should ask the PlaybackManager for state and call methods on it.

---

## 10. Spawn mpv in background

Current behavior:

```text
jbrowse waits while mpv runs
```

Future behavior:

```text
jbrowse stays open
mpv opens video window
jbrowse captures mpv output
UI remains usable
```

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

This likely belongs inside `PlaybackManager`.

Do this before Now Playing, mpv log page, or Jellyfin progress reporting.

---

## 11. mpv output/log page

Hotkey idea:

```text
Ctrl+G = mpv output/log page
```

Use a rolling buffer:

```python
collections.deque(maxlen=2000)
```

Maybe also write a log file:

```text
~/.cache/jbrowse/mpv.log
```

Useful external command:

```bash
tail -f ~/.cache/jbrowse/mpv.log
```

The in-app log page should support:

```text
q/backspace  close
↑/↓          scroll
PageUp/PageDown
Home/End
```

---

## 12. mpv IPC

Needed for real playback control.

mpv launch will eventually include a per-run local IPC socket option.

```text
/tmp/jbrowse-mpv-XXXX.sock
```

Needed commands/properties:

```text
time-pos
duration
pause
track-list
pause/play toggle
stop
seek
loadfile replace
set subtitle track
set audio track
```

This unlocks:

- Now Playing page
- pause/stop/seek controls
- replace-current-playback without restarting the whole app
- accurate Jellyfin playback reporting
- robust subtitle/audio switching
- static bitrate restart-at-current-position

Note:

When mpv IPC is implemented, update any stale-string / feature-guard checks for the new launch option.

---

## 13. Replace-current-playback prompt

If something is already playing and the user tries to play another item, ask first.

Dialog:

```text
Replace playback?

Currently playing:
Heavy Is the Head

Replace with:
Next Episode?

y replace | n cancel
```

Possible mpv implementation:

```text
loadfile NEW_URL replace
```

Potential complication:

Jellyfin playback reporting may be cleaner if the old session is explicitly stopped and a new one started. If `loadfile` causes Jellyfin reporting weirdness, use stop/relaunch internally.

---

## 14. Now Playing page

This should be the info page plus live playback state, not a separate tiny status page.

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

Hotkey idea:

```text
Ctrl+N = now playing
```

Behavior:

- Backspace from Now Playing returns to browser.
- Playback continues.
- If the user navigates to another item and presses play while something is active, show replace-current-playback prompt.

Needs:

- PlaybackManager
- background mpv
- mpv IPC for live progress

---

## 15. Pause / stop / seek controls

Possible controls:

```text
Space    pause/play
Ctrl+K   stop playback
, / .    seek backward/forward maybe
```

Needs mpv IPC first.

Terminal caveat:

Do not assume all modified keys work in every terminal. Test real key events before documenting them as final.

---

## 16. Jellyfin playback reporting

After mpv IPC exists, implement Jellyfin playback reporting.

Endpoints:

```text
playing start
playing progress
playing stopped
```

Use mpv IPC for accurate position:

```text
time-pos -> PositionTicks
```

Report state such as:

```text
ItemId
PositionTicks
IsPaused
CanSeek
```

Do not do this before IPC. Without IPC, final position is guesswork.

When this is implemented, update any stale-string / feature-guard checks for Jellyfin playback-reporting endpoints.

---

## 17. Final playback position save

When mpv exits or item is replaced:

```text
send final PositionTicks
send Playing/Stopped
```

Needs mpv IPC.

Goal:

- Jellyfin resume state should be accurate.
- Stopping playback should update watched/resume data.

---

## 18. Static bitrate selection

Possible quality options:

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

Bottom bar idea:

```text
subtitle: English - SUBRIP | quality: direct | style: jbrowse-ink.tcss
```

Implementation notes:

- Direct mode can keep the current static stream URL behavior.
- Bitrate-limited modes likely need Jellyfin transcoding URL parameters.
- Test against the user's actual Jellyfin server.
- Keep playback choices such as subtitle, quality, and later audio selection visible in the bottom status bar.

---

## 19. Change bitrate while playing

Not truly seamless.

Practical version:

```text
get current mpv time-pos
stop/replace stream
build new Jellyfin URL with new bitrate
restart at same position
```

Needs:

- mpv IPC
- static bitrate URL support
- PlaybackManager restart/replace logic

---

## 20. Audio picker

After subtitle picker and mpv IPC, add audio track selection.

Possible controls:

```text
a = audio picker
s = subtitle picker
```

Audio picker should mirror the subtitle picker:

```text
auto
English - Dolby Digital+ - 5.1 - Default
Japanese - AAC - Stereo
...
```

Robust implementation should use mpv IPC `track-list`.

---

## 21. Split the giant file

Do this later, after the app stabilizes further.

Possible structure:

```text
jbrowse/
  __main__.py
  config.py
  cache.py
  jellyfin.py
  models.py
  player.py
  ui.py
  themes.py
```

Do not do this too early. The single-file version is still useful while iterating.

Suggested timing:

- after PlaybackManager exists
- after non-blocking refresh exists
- after basic Now Playing exists

---

## 22. Stabilize name / packaging

Eventually settle on:

```text
jbrowse
README.md
pyproject.toml
jbrowse.conf.example
themes/
```

Possible future packaging:

```text
PKGBUILD
```

Do this after the core architecture is less volatile.

---

## Suggested order from here

```text
1. Real-server UI screenshot POC
2. Server-side safety guard
3. Configurable mpv command by format
4. Build files and Arch packaging skeleton
5. Non-blocking refresh
6. Cache refresh options
7. PlaybackManager
8. Background mpv
9. mpv log page
10. mpv IPC
11. Now Playing page
12. Replace playback prompt
13. Jellyfin playback reporting
14. Static bitrate/transcoding
15. Audio picker
16. Split into modules
17. Packaging/name cleanup
```

## Reminder: completed 0.0.25 baseline work

The following are already considered done and tested:

```text
full sort modes
persist sort_mode / sort_desc
regex search support
Batman themes
basic named page state
simple item cache
subtitle picker
README/docs
example config
gitignore
```
