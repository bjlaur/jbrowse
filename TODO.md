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

## Pending (after IPC features)

### Bottom bar progress bar
- After manual review: consider adding a visual `█░` progress bar to the bottom status bar during playback (not just text "playing: Title 1:23")
- Now Playing page already has a full bar; this would be a compact version for the browser bottom bar
- Defer until after manual testing confirms it's useful

### Server-side safety guard
- Keep track of code paths that can mutate Jellyfin/server state
- Playback session reporting is the only currently allowed server mutation
- Future metadata edits, deletes, favorites, manual played/unplayed toggles should be treated as server-side mutations
- Keep mutation-capable features behind explicit config/checks

### Audio picker
- After subtitle picker and mpv IPC, add audio track selection
- Hotkey: `a` for audio picker, `s` for subtitle picker
- Mirror subtitle picker UI
- Use mpv IPC `track-list` for robust implementation
- Investigate Jellyfin default audio/subtitle track selection

### Better help text / key map cleanup
- Suggested sections: Browsing, Search, Info, Playback, Themes, App
- Revisit reverse theme cycling (`Ctrl+Shift+X` not reliably distinguishable from `Ctrl+X`)

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
