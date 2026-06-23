# Release Plan — 0.0.34 (IPC Features)

## Status

**Branch**: `ipc-features`
**Current version**: `0.0.34`
**Status**: Code-complete. All IPC features implemented and tested. Merged `ipc-testing-fixes` branch. Awaiting final manual retest sign-off before tag.

---

## What's in 0.0.34

### Core IPC Features
1. **mpv IPC layer** — `PlaybackManager` connects via Unix socket; `ipc_get_property`, `ipc_set_property`, `ipc_command`, and high-level helpers
2. **Jellyfin playback reporting** — Accurate `/Sessions/Playing` (start/progress/stopped) via IPC, periodic every 5s
3. **Replace playback prompt** — "Already playing" / "Play this instead?" confirmation overlay
4. **Pause/stop/seek controls** — Space, `,`, `.`, Ctrl+K all via IPC
5. **Now Playing page** — Ctrl+N, progress bar, track info, quality flash
6. **Bitrate selection** — Ctrl+B cycles quality presets via Jellyfin transcoding, position preserved
7. **Playback control menu** — Ctrl+P global overlay (not Textual palette)

### Manual Testing Fixes (Rounds 1–4)
- Ctrl+P: `ENABLE_COMMAND_PALETTE = False` (correct Textual API)
- Replace prompt wording + same-item Enter shortcut
- Ctrl+K from Now Playing returns to previous_page
- Bottom bar live update (1s poll timer, `np:` prefix, 40-char truncation)
- Web URL overlay guards (not overwritten by IPC refresh)
- Info page progress auto-update without cursor movement
- Jump-to-time feature (`j` on Now Playing, IPC seek)
- Harness optimization: 1m24s → 31s
- Help key: `Ctrl+H`/`Ctrl+L` (removed `?` binding)
- Bottom bar poll: page-aware via `update_bottom_status()`
- MpV log scroll indicator: text-based `[####----] 42%` (SVG-safe)
- Now Playing progress bar: `[###---]` text format (SVG-safe)
- Playback-end page return: returns to `previous_page` instead of hardcoded browser

### Real IPC Tests
- `--real-mpv-bitrate`: quality cycles verified, position preserved
- `--real-mpv-jump`: seek to 30s/60s verified

### Docs & Screenshots
- Reorganized `docs/` into release-based structure (`release-0.0.34/`, `future-release/`)
- README screenshots updated: 10 best captures (added now-playing, playback-control, jump-to-time, replace-prompt; removed mpv-log, refreshing)
- Full theme gallery regenerated: 23 themes

---

## Release Checklist

### 1. Every Few Commits Checks — ✅ COMPLETE

**Documentation:**
- [x] `AGENTS.md` — Current Playback / IPC Status section reviewed
- [x] `TODO.md` — All completed items checked off, "Next" pointer updated
- [x] `CHANGELOG.md` — All 0.0.34 changes documented with testing summary
- [x] `README.md` — Version `0.0.34`, features list and controls current
- [x] `jbrowse.conf.example` — Includes `[playback]` section

**Tests & Screenshots:**
- [x] `python -m py_compile jbrowse.py` — Passes
- [x] `python -m py_compile tools/svg_screenshot_poc.py` — Passes
- [x] `python tools/svg_screenshot_poc.py --item otter` — All 29 SVG captures pass
- [x] Every new UI page/overlay/prompt has a corresponding harness capture

**Code Quality:**
- [x] `backspace` key works to go back/close on all overlays
- [x] IPC failures are graceful — fall back to existing behavior, never crash
- [x] `PlaybackManager` owns all IPC state; `BrowseApp` calls public methods only
- [x] No new Python packages needed — all stdlib

**Commit Discipline:**
- [x] Commit messages are short, imperative mood
- [x] Recent commits updated `AGENTS.md`, `TODO.md`, and `CHANGELOG.md`

### 2. Full Screenshot Harness — ✅ PASS

```bash
python tools/svg_screenshot_poc.py --item otter
```

Result: 29 captures pass.

### 3. IPC Smoke Test — ⏳ NEEDS REAL MPV + JELLYFIN

```bash
python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5
```

Requires real mpv + Jellyfin. Other agent is running manual retests.

### 4. Manual Release Check — ⏳ IN PROGRESS (other agent)

Items to verify manually:
- Open app, play an item — Now Playing auto-shows
- `Space` toggles pause, bottom bar updates
- `,` / `.` seek ±10s, position updates
- `Ctrl+B` quality cycles, 3-second flash on Now Playing
- `Ctrl+P` opens playback control menu (not Textual palette)
- `w` on info/Now Playing — overlay stays 3+ seconds
- Play → navigate → Enter — replace prompt appears with current wording
- `y` on replace — new item plays, old session stops
- `Ctrl+G` — mpv log with line numbers
- `Ctrl+K` — stops playback via IPC
- Bottom bar: `np: <title> – <MM:SS>` format
- Info page Progress auto-updates without cursor movement
- Info page backspace → browser
- Info → play → backspace from Now Playing → info
- `Ctrl+H` opens help overlay

### 5. Version Bump — ✅ DONE

`CLIENT_VERSION = "0.0.34"` in `jbrowse.py:77`.

### 6. Git Diff Review — ✅ DONE

79 commits ahead of main. 19 files changed. No stray debug prints or temporary code.

### 7. Ask User Before Committing/Pushing — ✅ (user handling push from terminal)

### 8. Major Release Steps (0.0.34 is a major release)

Per DEVELOPMENT.md — everything in "Release" above, plus:

- [x] **Full theme gallery**: `python tools/svg_screenshot_poc.py --item otter --all-themes` — ✅ 23 themes rendered, all pass
- [x] **Verify all themes render without errors in `docs/themes/`** — ✅ 23 SVG files present, no errors
- [ ] **Spot-check 3–4 theme SVGs visually for correct colors** — ⏳ Pending user review
- [x] **Copy updated screenshots from `tools/screenshot/` to `docs/screenshots/` for README use** — ✅ 10 screenshots selected and copied
- [x] **Review and update `README.md` from scratch if needed** — ✅ Features list, controls, config, and screenshots all updated
- [x] **Update `CHANGELOG.md` with full release notes and testing summary** — ✅ Every-few-commits and docs sections added
- [ ] **Ask user before pushing to remote** — ⏳ Pending (user handling push from terminal)

---

## Known Issues (Accepted for 0.0.34)

| Issue | Impact | Resolution |
|-------|--------|------------|
| Progress display uses mpv IPC time, Jellyfin runtime for total only | Minor cosmetic | Accept — mpv time and Jellyfin runtime can differ during transcoding |
| Replace prompt wording may need future revision | User preference | Deferred — track in TODO |
| `--real-mpv-bitrate` and `--real-mpv-jump` need real mpv + Jellyfin | Environment-specific | Developer-only; not a blocker |
| `?` key no longer opens help | User preference | `Ctrl+H` and `Ctrl+L` both work; revisit in 0.0.35 if needed |

---

## What's NOT in 0.0.34 (Deferred)

1. **Replace prompt wording revision** — User doesn't like current phrasing
2. **Audio picker** — `a` key to select audio tracks via IPC
3. **Better help text / key map cleanup** — Sectioned hotkey list
4. **Server-side safety guard** — Explicit mutation boundary tracking
5. **File splitting** — `jbrowse.py` (~4030 lines) → modules
6. **Test harness refactoring** — `svg_screenshot_poc.py` (~1085 lines) → modules
7. **Arch packaging** — `pyproject.toml`, `PKGBUILD`, desktop file
8. **Bottom bar visual progress bar** — `█░` in bottom bar (user deferred)

---

## Execution Steps (When Retesting Passes)

1. ~~Run `python tools/svg_screenshot_poc.py --item otter`~~ — ✅ 29/29 pass
2. ~~IPC smoke test~~ — ⏳ Other agent running manual retests
3. ~~Manual release check~~ — ⏳ Other agent running manual retests
4. **Ask user: "Ready to tag `v0.0.34`?"**
5. After approval: `git tag v0.0.34` (user pushes from terminal)

---

## Post-Release

After 0.0.34 is tagged:
1. Start 0.0.35 planning from `docs/future-release/release-plan.md`
2. Revisit replace prompt wording with user
3. Implement audio picker
4. Address items from `docs/release-0.0.34/for-next-release.md`
