# Release Plan — 0.0.34 (IPC Features)

## Status

**Branch**: `ipc-features`
**Current version**: `0.0.34` (already bumped)
**Status**: Code-complete. All IPC features implemented and tested. Ready for final verification and release.

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

### Real IPC Tests
- `--real-mpv-bitrate`: quality cycles verified, position preserved
- `--real-mpv-jump`: seek to 30s/60s verified

---

## Release Checklist

Per DEVELOPMENT.md "Release" section:

### 1. Every Few Commits Checks

**Documentation:**
- [ ] `AGENTS.md` — Current Playback / IPC Status section reviewed (looks current as of commit `33d62df`)
- [ ] `TODO.md` — All completed items checked off, "Next" pointer updated
- [ ] `CHANGELOG.md` — Review for completeness; consider adding any final Agent 2 round 4 items
- [ ] `README.md` — Version number is `0.0.34` (correct); features list and controls reference current
- [ ] `jbrowse.conf.example` — Includes `[playback]` section with `quality_presets` and `default_quality`

**Tests & Screenshots:**
- [x] `python -m py_compile jbrowse.py` — Passes
- [ ] `python -m py_compile tools/svg_screenshot_poc.py` — Verify
- [ ] `python tools/svg_screenshot_poc.py --item otter` — All 31 SVG captures pass (harness optimization round)
- [ ] Every new UI page/overlay/prompt has a corresponding harness capture — Yes (31 total)

**Code Quality:**
- [x] `backspace` key works to go back/close — Verified across all overlays
- [ ] IPC failures are graceful — Fall back to existing behavior, never crash
- [ ] `PlaybackManager` owns all IPC state; `BrowseApp` calls public methods only — Yes
- [ ] No new Python packages needed — All stdlib

**Commit Discipline:**
- [x] Commit messages are short, imperative mood
- [ ] Recent commits updated `AGENTS.md`, `TODO.md`, and `CHANGELOG.md` per project rule

### 2. Full Screenshot Harness

```bash
python tools/svg_screenshot_poc.py --item otter
```

Expected: 31 captures pass in ~31s.

### 3. IPC Smoke Test

Requires real mpv + Jellyfin (developer only):

```bash
python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5
```

### 4. Manual Release Check

From the checklist (items to verify manually):
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

### 5. Version Bump

Already done: `CLIENT_VERSION = "0.0.34"` in `jbrowse.py:77`.

### 6. Git Diff Review

```bash
git diff --stat main..ipc-features
# or: git diff --stat origin/main..HEAD
```

Review for any stray debug prints, temporary code, or unintended changes.

### 7. Ask User Before Committing/Pushing

Per project rule: **always ask before commit/push**.

---

## Known Issues (Pre-Release)

From CHANGELOG and test checklist:

| Issue | Impact | Resolution |
|-------|--------|------------|
| Progress display uses mpv IPC time, Jellyfin runtime for total only | Minor cosmetic | Accept — mpv time and Jellyfin runtime can differ during transcoding |
| MpV log scroll indicator (█░) doesn't render in SVG export | Harness-only | Accept — cosmetic, real terminal works fine |
| Replace prompt wording may need future revision | User preference | Deferred — track in TODO for 0.0.35 |
| Some harness captures are testing-only (not for README) | No user impact | Move nice-to-have captures to README set in 0.0.35 |
| `--real-mpv-bitrate` and `--real-mpv-jump` need real mpv + Jellyfin | Environment-specific | Developer-only; not a blocker for release |

---

## What's NOT in 0.0.34 (Deferred to 0.0.35+)

Per existing `release-plan.md` and `TODO.md`:

1. **Replace prompt wording revision** — User doesn't like current phrasing; discuss before implementing
2. **Audio picker** — `a` key to select audio tracks via IPC
3. **Better help text / key map cleanup** — Sectioned hotkey list
4. **README screenshot update** — Pick best 10 from 31 captures
5. **Server-side safety guard** — Explicit mutation boundary tracking
6. **File splitting** — `jbrowse.py` (4028 lines) → modules
7. **Test harness refactoring** — `svg_screenshot_poc.py` (1087 lines) → modules
8. **Arch packaging** — `pyproject.toml`, `PKGBUILD`, desktop file
9. **Bottom bar visual progress bar** — `█░` in bottom bar (user deferred)

---

## Special Notes for Release

### Version String Consistency
Verify these all say `0.0.34`:
- `jbrowse.py:77` — `CLIENT_VERSION = "0.0.34"`
- `README.md` — Version badge section (line ~11)
- `CHANGELOG.md` — Section header at top

### Screenshot Set
- Current `docs/screenshots/`: 8 files (browser, after-ctrl-x, help, info, mpv-log, refreshing, search, subtitles)
- 0.0.34 adds many more captures in `tools/screenshot/` — consider updating `docs/screenshots/` for 0.0.35

### Agent Notes Update
- `AGENTS.md` has 84-line "Current Playback / IPC Status" section — review for accuracy before tag
- "Next" pointer should reference 0.0.35 work

### Branch Strategy
- All code is on `ipc-features` branch, merged to `main` or about to be
- This plan sits on `planning-0.0.34` for review; it does NOT touch code, no merge conflicts expected

---

## Execution Steps (When Approved)

1. Run `python tools/svg_screenshot_poc.py --item otter` — verify all 31 pass
2. If developer available: run `--ipc-only --real --play-duration 5`
3. Run manual release check (10 items above)
4. Ask user: "Ready to commit and tag `v0.0.34`?"
5. After approval: `git tag v0.0.34 && git push origin v0.0.34` (only if user says to push)

---

## Post-Release (0.0.35 Prep)

After 0.0.34 is tagged:
1. Start fresh planning from `release-plan.md` (already exists for 0.0.35)
2. Revisit replace prompt wording with user
3. Implement audio picker
4. Update README screenshots from best captures
