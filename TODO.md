# TODO.md

## jbrowse TODO list

This file is the active roadmap. Completed items move to the changelog.
Only pending/unfinished work stays in the active sections below.

---

## Ground rules

- Keep `jbrowse.py` as the active single-file app until splitting it is clearly worth it.
- Keep the fast single-`Static` item renderer; do not return Textual `ListView` / `ListItem` media rows.
- Keep phases separate. Do not bundle subtitle selection, threaded refresh, player IPC, Now Playing, and Jellyfin progress reporting into one large change.
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
- **Every commit MUST update `AGENTS.md`, `TODO.md`, and `CHANGELOG.md`** to reflect the current state. No code commit without corresponding docs updates.

---

## Active: IPC Features (branch: `ipc-features`) — ALL COMPLETE

- [x] Phase 1: Low-level mpv IPC layer
- [x] Phase 2: Accurate Jellyfin playback reporting via IPC
- [x] Phase 3: Replace-current-playback prompt
- [x] Phase 4: Pause/stop/seek controls
- [x] Phase 5: Now Playing page (Ctrl+N)
- [x] Phase 6: Static bitrate selection (Ctrl+B)
- [x] Playback control menu (Ctrl+P)

---

## Manual Testing Fixes (0.0.34 re-test round) — ALL COMPLETE

- [x] Ctrl+P: set `ENABLE_COMMAND_PALETTE = False` at class level to prevent Textual command palette
- [x] Replace prompt: rewording to "Already playing" / "Play this instead?" / "y play  n cancel"
- [x] MpV log: added line numbers and scroll position indicator (█░ bar + percentage)
- [x] Now Playing backspace: returns to `previous_page` instead of hardcoded "browser"
- [x] Bottom bar: `np:` prefix, en dash separator, 40-char title limit (was 10)
- [x] Web URL overlay: poll timer skips re-rendering when overlay is visible
- [x] Info page Progress: fixed duplicate line (regex match), added 1s auto-update poll
- [x] Ctrl+B quality flash: 3-second on-page message when quality changes on Now Playing page
- [x] Ctrl+B seek back: after loadfile_replace, seeks to saved position via background thread
- [x] Replace prompt `n`: returns to info page instead of browser
- [x] Web URL overlay: render_info() and _render_now_playing() guard on _web_url_visible
- [x] Info page Progress regex: fixed from `Progress\s*:` to `Progress\s` (add_kv has no colon)
- [x] Harness: 31 captures, all pass; new views for all fixed items
- [x] Created ipc-retest-checklist.md with pass/fail status from manual testing
- [x] Created claude-didn't-listen.md report documenting missed harness tests
- [x] Bottom bar live poll: `_start_bottom_bar_poll()` timer updates widget every second
- [x] Ctrl+K from Now Playing: returns to previous_page (info) instead of browser
- [x] Same-item Enter: opens Now Playing directly, skips replace prompt
- [x] Jump-to-time feature: `j` key on Now Playing, overlay with IPC seek_to()
- [x] Jump-to-time overlay guards in _poll_now_playing() and _render_now_playing()
- [x] `--real-mpv-jump` test: verifies IPC seek to 30s and 60s
- [x] `ctrl-b-bitrate` and `jump-to-time` harness captures
- [x] Round 3 retest requests added to ipc-retest-checklist.md
- [x] `--real-mpv-bitrate` test fixed: hybrid approach (start playback before Textual harness)
- [x] `--real-mpv-jump` test fixed: wait for mpv to start, increased timeouts
- [x] Position preservation verified: video does NOT restart on quality change
- [x] 20→20→20 seek test passes
- [x] Help key: changed from `Ctrl+L`/`?` to `Ctrl+H`
- [x] Bottom bar poll: page-aware (respects subtitle status on info page)
- [x] MpV log scroll indicator: text-based `[####----] 42%` (SVG-safe)
- [x] Now Playing playback-end: returns to `previous_page` (info) not browser

---

## Pending (after IPC features)

### Replace prompt wording
- User doesn't like current wording: "Already playing" / "Play this instead?" / "Enter → replace  Backspace → cancel"
- Need to revise — consider something shorter
- Panel title is "Replace Playback" — could also be improved

### Jump to time feature
- ✅ Implemented for 0.0.34: press `j` on Now Playing page, type MM:SS or HH:MM:SS, Enter to jump via IPC seek_to()
- Overlay guards prevent poll timer from overwriting the jump-to-time UI
- `--real-mpv-jump` test verifies real IPC seek works correctly

### README screenshot update
- ✅ Done for 0.0.34: Selected best 10 from 31 harness captures per `docs/release-0.0.34/screenshot-analysis.md`
- Current 10 screenshots: browser, after-ctrl-x, help, info, search, subtitles, now-playing, playback-control, jump-to-time, replace-prompt
- Removed: mpv-log, refreshing (ranked lowest in analysis)

### Bottom bar progress bar
- Add a visual `█░` progress bar to the bottom status bar during playback (not just text "playing: Title 1:23")
- Now Playing page already has a full bar; this would be a compact version for the browser bottom bar
- Moved to fast follower (`docs/release-0.0.35/ipc-fastfollower-feature.md`)

### Server-side safety guard
- ✅ Implemented in 0.0.34: `post_server_mutation()` checks endpoint against `SERVER_MUTATION_OPERATIONS`
- Playback session reporting is the only currently allowed server mutation
- Future features must register here before mutating server state

### Audio picker
- After subtitle picker and mpv IPC, add audio track selection
- Hotkey: `a` for audio picker, `s` for subtitle picker
- Mirror subtitle picker UI
- Use mpv IPC `track-list` for robust implementation
- Investigate Jellyfin default audio/subtitle track selection

### Better help text / key map cleanup
- Suggested sections: Browsing, Search, Info, Playback, Themes, App
- Revisit reverse theme cycling (`Ctrl+Shift+X` not reliably distinguishable from `Ctrl+X`)
- Moved to fast follower (`docs/release-0.0.35/ipc-fastfollower-feature.md`)

### Split the giant file
- After app stabilizes further (after PlaybackManager, Now Playing exist)
- Possible: `jbrowse/__main__.py`, `config.py`, `cache.py`, `jellyfin.py`, `models.py`, `player.py`, `ui.py`, `themes.py`

### Build files and Arch packaging skeleton
- `pyproject.toml`, `PKGBUILD`
- LICENSE, Makefile, install script, desktop file, man page, shell completion
- Prefer Arch-friendly flow

### Stabilize name / packaging
- Settle on final file layout after core architecture is less volatile

### Rewrite README from scratch
- Very late cleanup item

### Windows portability release
- Later dedicated release

---

## Completed (moved to CHANGELOG.md for details)

- All 0.0.24–0.0.33 releases (see CHANGELOG.md)
- Phase 1: Low-level mpv IPC layer (committed `51bfb24`)
- Phase 2: Accurate Jellyfin playback reporting via IPC (committed `f37d1ea`)
- Phase 3: Replace-current-playback prompt (committed `7b391b0`)
- Phase 4: Pause/stop/seek controls via IPC (committed `2568d1e`)
- Phase 5: Now Playing page (committed in `c3b1bff`)
- Phase 6: Static bitrate selection (committed in `c3b1bff`)
- Playback control menu Ctrl+P (committed in `c3b1bff`)
- Auto-show Now Playing on playback start (committed in `f08d8cb`)
- Truncated bottom bar titles (committed in `f08d8cb`)
- Web URL hotkey `w` on info/now playing (committed in `f08d8cb`)
- Live IPC progress on info page (committed in `f08d8cb`)
- Screenshot harness: 12 captures, `--view` flag, fake playback (committed in `3297e68`, `f08d8cb`)
