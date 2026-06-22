# IPC Features Implementation Report

**Branch**: `ipc-features`
**Date**: 2026-06-22

---

## Part 1: Initial IPC Feature Implementation (Phases 1–6)

### Summary

Implemented a complete mpv IPC layer and 6 feature phases: low-level socket communication, accurate Jellyfin reporting, replace-playback prompt, pause/stop/seek controls, Now Playing page, static bitrate selection, and a global playback control menu.

### Prompts & Completion Status

1. **"is this working?"** — ✅
2. **"how do I change model and thinking harder stuff"** — ✅
3. **"read the current state of things... make a plan"** — ✅
4. **"we were in progress of working on the IPC stuff, but opcode was getting tedious"** — ✅
5. **"git reset"** — ✅
6. **"do we have a --real-mpv?"** — ✅ Added `--ipc-only` and `--play-duration` flags
7. **"make a plan for implementing the IPC stuff"** — ✅
8. **"implement while I sleep... make sure you add tests"** — ✅
9. **"put whatever you think makes sense in the bottom part.. mostly progress and playing state"** — ✅
10. **"when you test that... make sure you check server side"** — ✅
11. **"from global.. add a hotkey to show a menu"** — ✅ Ctrl+P playback control menu
12. **"don't forget to update the example conf"** — ✅
13. **"check to make sure all the help stuff was updated"** — ✅
14. **"EVERY commit MUST update AGENTS.md, TODO.md, and CHANGELOG.md"** — ✅
15. **"rename todo.md to TODO.md"** — ✅
16. **"it seems like there are tons of stuff in TODO that were completed"** — ✅
17. **"we're missing our 'manual release check'"** — ✅
18. **"I also need you to do a release checklist plan"** — ✅
19. **"don't forget the big report"** — ✅
20. **"about the progress bar at the bottom, make a note in todo"** — ✅
21. **"did you add new screenshots for any new screens?"** — ✅
22. **"update the ipc reports when done"** — ✅
23. **"make sure you were adding verifications for all your changes"** — ✅
24. **"do you really need to run the full harness every time?"** — ✅ Added `--view` flag
25. **"in agents... did you add that information so agents don't forget"** — ✅
26. **"continue until end of plan"** — ✅
27. **"redo the check on all documentation"** — ✅

### Commits (Part 1)

| Commit | Description |
|--------|-------------|
| `51bfb24` | Phase 1: Low-level mpv IPC layer |
| `f37d1ea` | Phase 2: Accurate Jellyfin reporting via IPC |
| `d0c4bda` | Docs update: Phase 1+2 complete |
| `7b391b0` | Phase 3: Replace-current-playback prompt |
| `2568d1e` | Phase 4: Pause/stop/seek controls |
| `841bd3a` | Docs update: Phase 3 complete |
| `c3b1bff` | Phase 6: Bitrate selection + playback control menu (Ctrl+P) |
| `3914a94` | Clean up TODO, update CHANGELOG/AGENTS with Phase 3-5 |
| `82d7b1e` | Docs update: Phase 6 complete |
| `fd39920` | Update README for 0.0.34 IPC features |
| `9e53d12` | Add release checklist to AGENTS.md |
| `880ef82` | Add IPC features implementation report (v1) |
| `3297e68` | Add screenshot harness captures for new UI screens + `--view` flag |

### Phase Details

**Phase 1** — Low-level IPC socket layer: `_ipc_connect`, `_ipc_send`, `_ipc_recv_response`, `ipc_get_property`, `ipc_set_property`, `ipc_command`, `toggle_pause`, `seek_to`, `seek_relative`, `loadfile_replace`, `set_track`, `stop_via_ipc`. Wired into `start_background()`, `stop_active()`, `run()`.

**Phase 2** — Accurate Jellyfin reporting: `position_ticks()` uses IPC `time-pos` first. Periodic progress reporter (5s). `playback_payload()` reads pause state from IPC.

**Phase 3** — Replace-current-playback prompt: Confirmation overlay with current + replacement item. Uses IPC `loadfile_replace` for seamless transition.

**Phase 4** — Pause/stop/seek: `Space` toggle, `,`/`. seek ±10s, `Ctrl+K` stop.

**Phase 5** — Now Playing page (Ctrl+N): Progress bar `█░`, track info from IPC `track-list`, quality label, 1s polling, auto-return on playback end.

**Phase 6** — Static bitrate selection (Ctrl+B): `[playback]` config section, transcoding URL with `MaxStreamingBitrate`.

**Playback Control Menu (Ctrl+P)** — Global overlay: pause, seek, quality, stop, now playing.

### Screenshot Harness (Part 1)

Added 4 new captures: now-playing, playback-control, replace-prompt, web-url. Added `--view <name>` flag for single-capture iteration. Added fake playback infrastructure (`_FakeProcess`, `_FakeIpcSock`, `_FAKE_IPC_VALUES`).

---

## Part 2: Manual Test Fixes

### Prompts & Completion Status

1. **"Now Playing should automatically show when playing something. Press q or backspace to return."** — ✅ `start_playback()` now auto-opens Now Playing. q/backspace returns to browser.

2. **"Rick.and.Morty.S09E02.Ricks.Days.Seven.Nights... is way too long. Find a way to make it max ~10 characters. Always show the S09E02 part."** — ✅ Added `_format_title_for_bar()` — shows e.g. `Rick and Morty - S09E02`. Truncates to 10 chars + `…` if needed.

3. **"Make a hotkey on info and on now playing that will show you the link to go to website for the episode."** — ✅ Added `w` key on info page and Now Playing page. Shows Jellyfin web URL overlay (`https://jellyfin.server/web/index.html#!/details?id=XXX`).

4. **"The Progress line on info page should update automatically with IPC results during playback."** — ✅ `render_info()` now injects live IPC position when viewing the currently-playing item.

5. **"Use short play-duration for regression tests, not the full thing every time."** — ✅ Default `--play-duration` changed to 0.5s. Note added to AGENTS.md.

6. **"Add screenshot tests for all new UI screens (w command, etc)."** — ✅ 12 total captures, all passing. Added web-url.svg capture.

7. **"do you really need to run the full harness every time?"** — ✅ `--view <name>` flag works for single captures.

8. **"Notep: make sure we are doing all this so agents don't forget in the future."** — ✅ Rules in AGENTS.md: every commit updates docs, every new UI screen gets a harness capture.

9. **"rename todo.md to TODO.md"** — ✅ Done.

10. **"it seems like there are tons of stuff in TODO that were completed"** — ✅ Cleaned up.

11. **"we're missing our 'manual release check'"** — ✅ Added to CHANGELOG.

12. **"do a release checklist plan"** — ✅ Added to AGENTS.md.

13. **"don't forget the big report"** — ✅ This document.

### Commits (Part 2)

| Commit | Description |
|--------|-------------|
| `88be9ef` | Note: use short play-duration for regression tests |
| `ca08575` | Remove duplicate prompts from report |
| `f08d8cb` | Manual test fixes: auto-now-playing, truncated titles, web URL, IPC progress, screenshots |
| `54d9a34` | Update report with manual test fixes |

### Detailed Changes (Part 2)

**Auto-show Now Playing**: `_do_start_playback()` calls `self.open_now_playing()` on success. The page starts polling IPC for live updates. q/backspace returns to browser.

**Truncated titles**: `_format_title_for_bar(item)` extracts show name (max 10 chars + `…`) and SxxExx pattern. Examples:
- `Rick.and.Morty.S09E02.Ricks.Days...` → `Rick and Morty - S09E02`
- `The.Land.Before.Time` → `The Land B…`

**Web URL hotkey (`w`)**: `_show_web_url()` builds `https://jellyfin.server/web/index.html#!/details?id=XXX`. Shows overlay with URL. Any key closes it.

**Live IPC progress on info page**: `render_info()` checks if the info item matches the currently playing item. If so, replaces the cached "Progress: X:XX / Y:YY" line with live IPC position.

**Screenshot harness**: 12 captures total (browser, after-ctrl-x, search, info, subtitles, help, mpv-log, refreshing, now-playing, playback-control, replace-prompt, web-url). `--view <name>` for single captures. Fake playback infrastructure for screens that need active playback state.

---

## Files Changed (Total)

| File | Changes |
|------|---------|
| `jbrowse.py` | +~900 lines: IPC layer, all 6 phases, playback control, web URL, title truncation, live IPC progress, help updates |
| `tools/svg_screenshot_poc.py` | +~200 lines: `--view` flag, 4 new captures, fake playback infrastructure |
| `jbrowse.conf.example` | Added `[playback]` section |
| `AGENTS.md` | Docs-update rule, release checklist, screenshot rules, IPC status, `--view` note |
| `TODO.md` | Complete rewrite — only pending items |
| `CHANGELOG.md` | 0.0.34 section with all phases + manual release check |
| `README.md` | Complete rewrite — version, features, controls, config |
| `docs/plans/ipc-features.md` | Implementation plan |
| `docs/reports/ipc-features-report.md` | This report |

---

## Testing Summary

- **Compile**: `python -m py_compile jbrowse.py tools/svg_screenshot_poc.py` — clean
- **Screenshots**: `python tools/svg_screenshot_poc.py --item otter` — 12/12 pass
- **Single capture**: `--view now-playing`, `--view replace-prompt`, `--view web-url` all work ✅
- **IPC smoke**: `--ipc-only --real --play-duration 0.5` — passes ✅
- **Server-side**: Jellyfin reports accepted with accurate positions ✅

---

## Known Gaps / Manual Release Check Items

1. Play an item — Now Playing page should auto-show
2. Press `Space` — toggles pause, bottom bar updates
3. Press `,` / `.` — seeks ±10s
4. Press `Ctrl+B` — quality cycles
5. Press `Ctrl+P` — playback control menu appears
6. Press `w` on info/now playing — web URL overlay appears
7. Play item, navigate to another, press Enter — replace prompt appears
8. Press `y` — new item starts, old session stopped
9. Press `Ctrl+G` during playback — mpv log page works
10. Press `Ctrl+K` — stops playback via IPC
11. Bottom bar shows truncated title like `Rick and Morty - S09E02`
12. Info page Progress line updates live from IPC during playback
13. **Bottom bar visual progress bar** — needs manual review (text-only for now, TODO item added)

---

## What's Next (from TODO.md)

1. Bottom bar visual progress bar (after manual review)
2. Server-side safety guard
3. Audio picker
4. Better help text / key map cleanup
5. Split into modules (later)
6. Build/packaging/Arch PKGBUILD
