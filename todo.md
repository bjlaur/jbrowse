# todo.md



## jbrowse TODO list, post-0.0.32

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
- real-server UI screenshot POC
- configurable `mpv_cmd` playback template
- non-blocking manual refresh
- automatic background refresh after cached startup
- periodic background refresh while recently active
- minimal Jellyfin playback reporting
- background mpv while jbrowse stays open
- background refresh after playback returns
- numbered theme cycle order
- SVG screenshot harness with basic content checks
- mpv command/output viewer
- documented current server-side mutation boundary
- current config/example/gitignore/docs

Use this file as the roadmap and release-history checklist.

---

## Ground rules

- Keep `jbrowse.py` as the active single-file app until splitting it is clearly worth it.
- Keep the fast single-`Static` item renderer; do not return to Textual `ListView` / `ListItem` media rows.
- Keep phases separate. Do not bundle subtitle selection, threaded refresh, player IPC, Now Playing, and Jellyfin progress reporting into one large change.
- Do not add player config or mpv IPC launch options until the corresponding roadmap section is being implemented.
- Keep completed todo items marked as done instead of deleting them.
- Add a small `CHANGELOG.md` entry with a tiny testing summary after each release.
- When a change is visible in the UI, consider adding or updating a screenshot POC step so we can tell the UI changed over time.
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
- [x] ~~Real-server UI screenshot POC.~~ Released in `0.0.26`.
- [x] ~~Single configurable `mpv_cmd` playback template.~~ Released in `0.0.27`.
- [x] ~~Document current server-side mutation boundary.~~ Released in `0.0.27`.
- [x] ~~Non-blocking manual refresh and cached-startup background refresh.~~ Released in `0.0.28`.
- [x] ~~Periodic refresh while recently active.~~ Released in `0.0.29`.
- [x] ~~PlaybackManager with minimal Jellyfin playback reporting.~~ Released in `0.0.30`.
- [x] ~~Background refresh after playback returns.~~ Released in `0.0.30`.
- [x] ~~Numbered theme cycle order and SVG screenshot harness checks.~~ Released in `0.0.31`.
- [x] ~~Background mpv while jbrowse stays open.~~ Released in `0.0.32`.
- [x] ~~mpv output page.~~ Released in `0.0.32`.

---

## 1. mpv IPC

Needed for accurate playback control and playback reporting.

PlaybackManager should eventually own:

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

- accurate Jellyfin playback reporting
- Now Playing page
- pause/stop/seek controls
- replace-current-playback without restarting the whole app
- robust subtitle/audio switching
- static bitrate restart-at-current-position

---

## 2. Background mpv follow-ups

Likely next release: `0.0.33` should be a small background playback cleanup release, not full mpv IPC.

Current behavior:

```text
jbrowse stays open
mpv opens video window
jbrowse captures mpv output
UI remains usable
```

Follow-up ideas:

```text
stop active mpv from jbrowse
handle app quit while playback is active
switch/focus mpv output view
```

Suggested `0.0.33` scope:

- Add a simple hotkey to stop active mpv from `jbrowse`.
- Make quitting while mpv is active deliberate.
- Lightly polish the `Ctrl+G` mpv output page.
- Discuss whether to add an undocumented local config version guard before future `jbrowse.conf` writes.
- Update the screenshot harness if the log page visual changes.
- Test with compile, SVG harness, and fake playback smoke.

Config guard idea to discuss before implementing:

- Add a private/undocumented config version marker to real `jbrowse.conf`; do not put it in `jbrowse.conf.example`.
- Update that marker during releases when local config changes are expected.
- Before `jbrowse` writes config, compare the running app's expected marker with the file's current marker.
- Refuse or warn if an older still-running `jbrowse` instance might overwrite newer config changes.
- Keep this very small if it happens; the idea may be unnecessary or replaced by a better stale-write guard.

Keep IPC-specific work separate.

---

## 3. Live mpv output/log page

Current behavior:

```text
Ctrl+G shows a live rolling mpv output buffer while playback is active
```

Hotkey idea:

```text
Shift+Tab = maybe switch/focus mpv output once IPC/background playback exists
```

Terminal caveat: verify the real Textual key event for `Shift+Tab` before documenting it as final.

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

Follow-up:

- Improve the `mpv log` page presentation; current version is useful but rough.

---

## 4. Better help text / key map cleanup

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

## 5. Server-side safety guard

Goal: keep track of code paths that can mutate Jellyfin/server state before we add playback reporting or other write APIs.

Current expectation:

- Login, fetch, stream URL construction, cache writes, and screenshot harvesting should not modify media metadata or playback state on the Jellyfin server.
- Playback session reporting is now intentional. Future metadata edits, deletes, favorites, and manual played/unplayed toggles should be treated as server-side mutations.

Implementation notes:

- Keep mutation-capable features behind explicit config/checks.
- Document mutation-capable endpoints before adding them.
- Current `0.0.30` state includes playback session reporting; add real guards when broader mutation-capable features are implemented.

---

## 6. Future mpv command profiles

The app currently has one configurable `mpv_cmd` template.

Later, if one command is not enough, consider named/profiled mpv commands.

Implementation notes:

- Do not add format detection unless there is a clear real-world need.
- Do not add mpv IPC as part of this task.
- Do not add background playback as part of this task.

## 7. Accurate Jellyfin playback reporting

Needs mpv IPC for accurate position.

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

This improves:

- accurate Jellyfin playback reporting
- resume position
- watched-state decisions
- progress updates during long playback

Note:

When mpv IPC is implemented, update any stale-string / feature-guard checks for the new launch option.

---

## 8. Replace-current-playback prompt

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

## 9. Now Playing page

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

## 10. Pause / stop / seek controls

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

## 11. Jellyfin playback reporting notes

Minimal playback reporting exists as of `0.0.30`. After mpv IPC exists, make it accurate.

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

## 12. Final playback position save

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

## 13. Static bitrate selection

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

## 14. Change bitrate while playing

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

## 15. Audio picker

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

## 16. Split the giant file

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

## 17. Build files and Arch packaging skeleton

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

## 18. Stabilize name / packaging

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
1. mpv IPC
2. Accurate Jellyfin playback reporting
3. Background mpv
4. mpv log page
5. Now Playing page
6. Replace playback prompt
7. Static bitrate/transcoding
8. Audio picker
9. Better help text / key map cleanup
10. Split into modules
11. Build files and Arch packaging skeleton
12. Packaging/name cleanup
```

## Reminder: completed 0.0.26 baseline work

The following are already considered done and tested:

```text
full sort modes
persist sort_mode / sort_desc
regex search support
Batman themes
basic named page state
simple item cache
subtitle picker
real-server UI screenshot POC
configurable mpv_cmd playback template
non-blocking manual refresh
automatic background refresh after cached startup
periodic background refresh while recently active
minimal Jellyfin playback reporting
background refresh after playback returns
documented server-side mutation boundary
README/docs
example config
gitignore
```
