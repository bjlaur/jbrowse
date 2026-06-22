# IPC Features Implementation Report

**Branch**: `ipc-features`
**Date**: 2026-06-22
**Status**: All 6 phases complete + playback control menu + screenshot harness updates + manual test fixes

---

## Summary

Implemented a complete mpv IPC (Inter-Process Communication) layer and 6 feature phases on top of it, transforming jbrowse from a basic mpv launcher into a full-featured Jellyfin TUI with accurate playback reporting, live progress tracking, quality controls, and a Now Playing page. Also added a global playback control menu, comprehensive screenshot harness coverage, a release checklist, and manual test fixes (auto-show Now Playing, truncated titles, web URL hotkey, IPC progress updates).

---

## All User Prompts & Completion Status

1. **"is this working?"** — ✅ Confirmed OWL operational.

2. **"how do I change model and thinking harder stuff"** — ✅ Explained /config and /reasoning commands.

3. **"read the current state of things... make a plan"** — ✅ Read entire codebase, wrote plan at `docs/plans/ipc-features.md`.

4. **"we were in progress of working on the IPC stuff, but opcode was getting tedious"** — ✅ Acknowledged; rebuilt IPC layer from scratch after git reset.

5. **"git reset"** — ✅ Reset to clean slate at `d56a619`.

6. **"do we have a --real-mpv?"** — ✅ Confirmed it exists. Added `--ipc-only` and `--play-duration` flags to test harness.

7. **"make a plan for implementing the IPC stuff"** — ✅ Wrote comprehensive 6-phase plan.

8. **"implement while I sleep... spawn agents... make sure you add tests and do smoke testing"** — ✅ Implemented all phases with testing after each.

9. **"put whatever you think makes sense in the bottom part.. mostly progress and playing state"** — ✅ Updated bottom status bar with live IPC position. Added quality label to Now Playing page.

10. **"when you test that... make sure you check that it was updated server side"** — ✅ Verified Jellyfin reports accepted with accurate positions in playback log.

11. **"from global (info page and browse page etc) we should be able to control state as well. Add a hotkey to show a menu"** — ✅ Added Ctrl+P playback control menu.

12. **"don't forget to update the example conf"** — ✅ Added `[playback]` section to `jbrowse.conf.example`.

13. **"check to make sure all the help stuff was updated in jbrowse"** — ✅ Help page updated with all new hotkeys. Verified in SVG.

14. **"EVERY every commit you do should have the corresponding changes in changes.md, todo.md, and AGENTS.md"** — ✅ Rule added to AGENTS.md. Followed for all subsequent commits.

15. **"rename todo.md to TODO.md"** — ✅ Done.

16. **"it seems like there are tons of stuff in TODO that were completed"** — ✅ Completely rewrote TODO.md — only pending items remain.

17. **"we're missing our 'manual release check' on the 0.0.34 section"** — ✅ Added comprehensive manual release check to CHANGELOG.

18. **"I also need you to do a release checklist plan and add that to AGENTS.MD"** — ✅ Added full release checklist.

19. **"don't forget the big report into an md file"** — ✅ This document.

20. **"about the progress bar at the bottom, let me do some manual use and review that idea. make a note in todo to follow up"** — ✅ Added TODO item for bottom bar progress bar follow-up.

21. **"did you add new screenshots for any new screens into the test harness?"** — ✅ Added 3 new captures (now-playing, playback-control, replace-prompt). Total: 11.

22. **"update the ipc reports when done"** — ✅ Updated IPC status in AGENTS.md after each phase.

23. **"make sure you were adding verifications for all your changes that can be verified visually into the test harness"** — ✅ Every new UI screen has expected text checks. Rule added to AGENTS.md.

24. **"do you really need to run the full harness every time? we should have the ability to just run what we need"** — ✅ Added `--view <name>` flag for single-capture iteration.

25. **"ok, gonna go to the store. I expect another full report"** — ✅ This document.

26. **"when you're done with everything generate a full report"** — ✅ This document.

27. **"in... in agents... did you add that information about making sure that we are doing all this so agents don't forget"** — ✅ Rule added: "Every commit MUST update AGENTS.md, TODO.md, and CHANGELOG.md".

28. **"continue until end of plan"** — ✅ All 6 phases + extras complete.

29. **"and since that was a change you need to redo the check on all documentation and help page in jbrowse"** — ✅ All docs updated after each change.

30. **"Note: auto-show Now Playing page when playback starts, q/backspace to return"** (from manual testing) — ✅ `start_playback()` now auto-opens Now Playing. Bottom bar shows truncated title like `Rick and Morty - S09E02`.

31. **"Truncate long filenames in bottom bar — show ~10 chars + SxxExx"** (from manual testing) — ✅ Added `_format_title_for_bar()` — shows e.g. `Rick and Morty - S09E02`.

32. **"Add hotkey on info and now playing to show web link for the episode"** (from manual testing) — ✅ Added `w` key on info page and Now Playing page. Shows Jellyfin web URL overlay.

33. **"Update info page Progress line in real-time from IPC during playback"** (from manual testing) — ✅ `render_info()` now injects live IPC position when viewing the currently-playing item.

34. **"Note: use short play-duration for regression tests"** — ✅ Default `--play-duration` changed to 0.5s. Note added to AGENTS.md.

35. **"Did you add new screenshots for any new screens into the test harness?"** — ✅ Added 4 new captures: now-playing, playback-control, replace-prompt, web-url. Total: 12.

36. **"do you really need to run the full harness every time?"** — ✅ Added `--view <name>` flag for single-capture iteration.

37. **"make sure you add screenshot tests and verifications for all these new features"** — ✅ All new UI screens have harness captures with expected text checks.

---

## Commits on `ipc-features` branch

| Commit | Description |
|--------|-------------|
| `51bfb24` | Phase 1: Low-level mpv IPC layer + `--ipc-only`/`--play-duration` flags |
| `f37d1ea` | Phase 2: Accurate Jellyfin reporting via IPC |
| `d0c4bda` | Docs update: Phase 1+2 complete |
| `7b391b0` | Phase 3: Replace-current-playback prompt |
| `2568d1e` | Phase 4: Pause/stop/seek controls |
| `841bd3a` | Docs update: Phase 3 complete |
| `c3b1bff` | Phase 6: Bitrate selection + playback control menu (Ctrl+P) |
| `3914a94` | Clean up TODO, update CHANGELOG and AGENTS with Phase 3-5 |
| `82d7b1e` | Docs update: Phase 6 complete |
| `fd39920` | Update README for 0.0.34 IPC features |
| `9e53d12` | Add release checklist to AGENTS.md |
| `880ef82` | Add IPC features implementation report (v1) |
| `3297e68` | Add screenshot harness captures for new UI screens + `--view` flag |
| `88be9ef` | Note: use short play-duration for regression tests |
| `ca08575` | Remove duplicate prompts from report |
| `96d903f59` | Note: use short play-duration for regression tests |
| `f08d8cb` | Manual test fixes: auto-now-playing, truncated titles, web URL, IPC progress, screenshots |

---

## Phase-by-Phase Details

### Phase 1: Low-Level IPC Layer
**Commit**: `51bfb24`

- `PlaybackManager` connects to mpv via `--input-ipc-server` Unix socket
- Socket connect with retry, JSON command/response with request_id matching
- Public API: `ipc_get_property`, `ipc_set_property`, `ipc_command`
- High-level helpers: `toggle_pause`, `seek_to`, `seek_relative`, `loadfile_replace`, `set_track`, `stop_via_ipc`
- `stop_active()` tries IPC `stop` first, falls back to `terminate()`
- `--ipc-only` and `--play-duration` flags on screenshot harness

### Phase 2: Accurate Jellyfin Playback Reporting
**Commit**: `f37d1ea`

- `position_ticks()` uses IPC `time-pos` first, falls back to wall-clock
- Periodic progress reporter thread sends `/Sessions/Playing/Progress` every 5s
- `playback_payload()` reads `pause` state from IPC
- Bottom status bar shows live state with position
- Verified server-side: all Jellyfin reports accepted with accurate positions

### Phase 3: Replace-Current-Playback Prompt
**Commit**: `7b391b0`

- Confirmation overlay when playing over active playback
- Shows current + replacement item, `y replace | n cancel`
- On confirm: stops old Jellyfin session, uses IPC `loadfile_replace`

### Phase 4: Pause/Stop/Seek Controls
**Commit**: `2568d1e`

- `Space` toggles pause/play via IPC
- `,` / `.` seek -10s / +10s via IPC
- Help page updated

### Phase 5: Now Playing Page
**Commit**: (in `c3b1bff`)

- New `now_playing` page, opened with `Ctrl+N`
- Progress bar with `█░` blocks, position/duration from IPC
- Track info from IPC `track-list`, quality label
- 1-second polling timer, auto-returns to browser on playback end

### Phase 6: Static Bitrate Selection
**Commit**: `c3b1bff`

- `[playback]` config section with `quality_presets` and `default_quality`
- `Ctrl+B` cycles quality presets
- Uses `loadfile_replace` with transcoding URL for seamless quality change

### Playback Control Menu (Ctrl+P)
**Commit**: `c3b1bff`

- Global overlay accessible from any page
- Shows playback state, position/duration, quality
- Key actions: Space pause, `,`/`. seek, Ctrl+B quality, Ctrl+K stop, Ctrl+N now playing

---

## Screenshot Harness Updates

**Commit**: `3297e68`

### New Captures Added
- `now-playing.svg` — Now Playing page with progress bar, track info, quality
- `playback-control.svg` — Ctrl+P menu with all playback controls
- `replace-prompt.svg` — Replace confirmation overlay

### Total Captures: 11
browser, after-ctrl-x, search, info, subtitles, help, mpv-log, refreshing, now-playing, playback-control, replace-prompt

### New `--view` Flag
Run a single capture for fast iteration:
```bash
python tools/svg_screenshot_poc.py --view now-playing
python tools/svg_screenshot_poc.py --view replace-prompt
python tools/svg_screenshot_poc.py --view playback-control
```

### Fake Playback Infrastructure
- `_setup_fake_playback()` — sets up PlaybackManager with fake active playback
- `_FakeProcess` — fake subprocess that reports as "running"
- `_FakeIpcSock` — fake IPC socket
- `_FAKE_IPC_VALUES` — plausible property values (time-pos, duration, pause, track-list)

---

## Files Changed

| File | Changes |
|------|---------|
| `jbrowse.py` | +~800 lines: IPC layer, all 6 phases, playback control menu, help updates |
| `tools/svg_screenshot_poc.py` | +~150 lines: `--view` flag, 3 new captures, fake playback infrastructure |
| `jbrowse.conf.example` | Added `[playback]` section |
| `AGENTS.md` | Docs-update rule, release checklist, `--view` flag note, IPC status |
| `TODO.md` | Complete rewrite — cleaned up, only pending items |
| `CHANGELOG.md` | 0.0.34 section with all phases + manual release check |
| `README.md` | Complete rewrite — version, features, controls, config |
| `docs/plans/ipc-features.md` | Implementation plan |
| `docs/reports/ipc-features-report.md` | This report |

---

## Testing Summary

All tests passed on every phase:

- **Compile**: `python -m py_compile jbrowse.py tools/svg_screenshot_poc.py` — clean
- **Screenshots**: `python tools/svg_screenshot_poc.py --item otter` — 11/11 pass
- **IPC smoke**: `python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5` — time-pos ≈ elapsed ✅
- **Server-side**: Verified Jellyfin reports accepted in playback log ✅
- **Single capture**: `--view now-playing`, `--view replace-prompt`, `--view playback-control` all work ✅

---

## Known Gaps / Manual Release Check Items

1. Play an item, press `Ctrl+N` — Now Playing page shows live progress bar
2. Press `Space` — toggles pause, bottom bar state updates
3. Press `,` / `.` — seeks ±10s, position updates
4. Press `Ctrl+B` — quality cycles, status message shown
5. Press `Ctrl+P` — playback control menu appears
6. Play item, navigate to another, press Enter — replace prompt appears
7. Press `y` — new item starts, old session stopped
8. Press `Ctrl+G` during playback — mpv log page works
9. Press `Ctrl+K` — stops playback via IPC
10. **Bottom bar progress bar** — needs manual review (text-only for now, TODO item added)

---

## What's Next (from TODO.md)

1. Bottom bar progress bar (after manual review)
2. Server-side safety guard
3. Audio picker
4. Better help text / key map cleanup
5. Split into modules (later)
6. Build/packaging/Arch PKGBUILD
