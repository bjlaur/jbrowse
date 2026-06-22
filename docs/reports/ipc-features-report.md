# IPC Features Implementation Report

**Branch**: `ipc-features`
**Date**: 2026-06-22
**Status**: All 6 phases complete + playback control menu

---

## Summary

Implemented a complete mpv IPC (Inter-Process Communication) layer and 6 feature phases on top of it, transforming jbrowse from a basic mpv launcher into a full-featured Jellyfin TUI with accurate playback reporting, live progress tracking, quality controls, and a Now Playing page.

---

## User Prompts & Requests (in order received)

1. **"is this working?"** — Confirmed OWL is operational.
2. **"how do I change model and thinking harder stuff"** — Explained /config and /reasoning commands.
3. **"read the current state of things... make a plan"** — Read entire codebase, wrote plan for IPC implementation.
4. **"we were in progress of working on the IPC stuff, but opcode was getting tedious"** — Acknowledged; the low-level socket code was already done but got lost in git reset.
5. **"git reset"** — Reset to clean slate at `d56a619`.
6. **"do we have a --real-mpv?"** — Yes, confirmed it exists. Added `--ipc-only` flag and `--play-duration` flag to test harness.
7. **"make sure you add tests and do smoke testing"** — Added verification after each phase.
8. **"put whatever you think makes sense in the bottom part.. mostly progress and playing state"** — Updated bottom status bar to show live IPC playback state.
9. **"when you test that... make sure you check that it was updated server side"** — Verified Jellyfin reports in local playback log.
10. **"from global (info page and browse page etc) we should be able to control state as well. Add a hotkey to show a menu"** — Added Ctrl+P playback control menu.
11. **"don't forget to update the example conf"** — Added `[playback]` section to `jbrowse.conf.example`.
12. **"check to make sure all the help stuff was updated in jbrowse"** — Updated help page with all new hotkeys.
13. **"EVERY every commit you do should have the corresponding changes in changes.md, todo.md, and AGENTS.md"** — Established discipline; added rule to AGENTS.md.
14. **"rename todo.md to TODO.md"** — Done.
15. **"it seems like there are tons of stuff in TODO that were completed"** — Cleaned up TODO.md to only show pending items.
16. **"we're missing our 'manual release check' on the 0.0.34 section"** — Added manual release check to CHANGELOG.
17. **"I also need you to do a release checklist plan and add that to AGENTS.MD"** — Added comprehensive release checklist.
18. **"don't forget the big report into an md file"** — This document.

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

---

## Phase-by-Phase Details

### Phase 1: Low-Level IPC Layer
**Files**: `jbrowse.py`, `tools/svg_screenshot_poc.py`

- Added `default_mpv_ipc_path()` — generates unique temp socket path
- Added IPC state to `PlaybackManager.__init__`: `_ipc_sock`, `_ipc_lock`, `_ipc_request_id`, `ipc_socket_path`
- `_ipc_connect(path, timeout=5.0)` — connects to Unix socket with retry
- `_ipc_send(command, timeout=3.0)` — sends JSON command, returns parsed response
- `_ipc_recv_response(req_id, timeout)` — reads socket lines until matching request_id
- `_ipc_get_number(property_name)` — gets numeric property
- `ipc_get_property(name)` / `ipc_set_property(name, value)` / `ipc_command(*args)` — public API
- High-level helpers: `toggle_pause()`, `seek_to()`, `seek_relative()`, `loadfile_replace()`, `set_track()`, `stop_via_ipc()`
- `_ipc_close()` — cleanup
- Wired into `start_background()`, `stop_active()`, `wait_for_background_playback()`, `run()`
- Added `--ipc-only` and `--play-duration` flags to screenshot harness

**Testing**: 8/8 screenshots pass. IPC smoke test: time-pos ≈ elapsed time ✅

---

### Phase 2: Accurate Jellyfin Playback Reporting
**Files**: `jbrowse.py`

- `position_ticks()` now tries IPC `time-pos` first, falls back to wall-clock
- Added `_progress_reporter_worker()` — polls IPC every 5s, sends Jellyfin progress
- Added `_start_progress_reporter()` / `_stop_progress_reporter()` — thread lifecycle
- `playback_payload()` reads `pause` state from IPC instead of hardcoding `False`
- Bottom status bar shows live state: `playing/paused: <title> <MM:SS>`

**Testing**: Verified server-side — Jellyfin start/progress/stopped reports all accepted with accurate positions in local playback log ✅

---

### Phase 3: Replace-Current-Playback Prompt
**Files**: `jbrowse.py`

- `start_playback()` checks if something is already active
- Shows confirmation overlay: "Currently playing: X / Replace with: Y? y/n"
- On confirm: stops old Jellyfin session, uses IPC `loadfile_replace` for seamless transition
- On cancel: returns to browser

**Testing**: 8/8 screenshots pass ✅

---

### Phase 4: Pause/Stop/Seek Controls
**Files**: `jbrowse.py`

- `Space` — toggles pause/play via IPC
- `,` / `.` — seek -10s / +10s via IPC `seek_relative()`
- `Ctrl+K` — already existed for stop (unchanged)
- Help page updated with new controls

**Testing**: 8/8 screenshots pass. Help SVG shows new controls ✅

---

### Phase 5: Now Playing Page
**Files**: `jbrowse.py`

- New `now_playing` page, opened with `Ctrl+N`
- Progress bar with `█░` blocks, position/duration from IPC
- State display: playing/paused, video/audio/subtitle track info from IPC `track-list`
- 1-second polling timer for live updates
- Auto-returns to browser when playback ends while on this page
- `now_playing_scroll` added to `UIState`

**Testing**: 8/8 screenshots pass ✅

---

### Phase 6: Static Bitrate Selection
**Files**: `jbrowse.py`, `jbrowse.conf.example`

- `[playback]` config section: `quality_presets` and `default_quality`
- `Ctrl+B` cycles through quality presets (direct → 40mbps → 20mbps → ... → 2mbps)
- On change: gets `time-pos` via IPC, builds transcoding URL with `MaxStreamingBitrate`, uses `loadfile_replace`
- Quality shown in Now Playing page and playback control menu
- `Config` dataclass updated with `quality_presets` and `default_quality`
- `load_cfg()` reads new section with sensible defaults

**Testing**: 8/8 screenshots pass. Config loads correctly ✅

---

### Playback Control Menu (Ctrl+P)
**Files**: `jbrowse.py`

- Global overlay accessible from any page via `Ctrl+P`
- Shows current playback state: title, position/duration, quality
- Key actions: Space pause, `,`/`. seek, Ctrl+B quality, Ctrl+K stop, Ctrl+N now playing
- `q`/`Escape`/`backspace` closes and returns to browser

**Testing**: 8/8 screenshots pass ✅

---

## Files Changed

| File | Changes |
|------|---------|
| `jbrowse.py` | +~650 lines: IPC layer, all 6 phases, playback control menu, help updates |
| `tools/svg_screenshot_poc.py` | Added `--ipc-only`, `--play-duration`, fixture config update |
| `jbrowse.conf.example` | Added `[playback]` section |
| `AGENTS.md` | Added docs-update rule, release checklist, IPC status |
| `TODO.md` | Complete rewrite — cleaned up completed items, only pending remains |
| `CHANGELOG.md` | Added 0.0.34 section with all phases + manual release check |
| `README.md` | Complete rewrite — updated version, features, controls, config |
| `docs/plans/ipc-features.md` | Implementation plan document |

---

## Testing Summary

All tests passed on every phase:

- **Compile**: `python -m py_compile jbrowse.py tools/svg_screenshot_poc.py` — clean
- **Screenshots**: `python tools/svg_screenshot_poc.py --item otter` — 8/8 pass
- **IPC smoke**: `python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5` — time-pos ≈ elapsed ✅
- **Server-side**: Verified Jellyfin reports accepted in `~/.cache/jbrowse/mpv.out-*` log ✅

---

## Known Gaps / Manual Release Check Items

The following need manual verification (can't be automated):

1. Play an item, press `Ctrl+N` — Now Playing page shows live progress bar
2. Press `Space` — toggles pause, bottom bar state updates
3. Press `,` / `.` — seeks ±10s, position updates
4. Press `Ctrl+B` — quality cycles, status message shown
5. Press `Ctrl+P` — playback control menu appears with all controls
6. Play item, navigate to another, press Enter at info — replace prompt appears
7. Press `y` — new item starts, old Jellyfin session stopped
8. Press `Ctrl+G` during playback — mpv log page works
9. Press `Ctrl+K` — stops playback via IPC

---

## What's Next (from TODO.md)

1. Server-side safety guard
2. Audio picker
3. Better help text / key map cleanup
4. Split into modules (later)
5. Build/packaging/Arch PKGBUILD
