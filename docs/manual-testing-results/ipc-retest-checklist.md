# IPC Re-test Checklist — 0.0.34

## Legend

- [x] = passed
- [ ] = not tested yet
- **FAIL** = broken, needs fix

---

## Round 1 — Initial Fixes

| # | Test | Harness | Manual | Why no harness? | Notes |
|---|------|---------|--------|-----------------|-------|
| 1 | Open app, play an item — Now Playing page auto-shows | [x] | [x] | — | |
| 2 | Press `Space` — toggles pause, bottom bar updates | [x] | [x] | — | |
| 3 | Press `,` / `.` — seeks ±10s, position updates in bottom bar | [x] | [x] | — | |
| 4 | Press `Ctrl+B` — quality cycles, 3-second flash on Now Playing page | [x] | [ ] | — | **Needs server log check** — did it actually transcode? Video restarts (should be seamless). **FIX APPLIED**: seek back after loadfile_replace. |
| 5 | Press `Ctrl+P` — playback control menu appears (not Textual palette) | [x] | [ ] | — | **FAIL** — Textual palette still appears. Needs real-keyboard test. |
| 6 | Press `Ctrl+K` — stops playback via IPC | [x] | [x] | — | Pass. |
| 7 | Press `w` on info page — web URL overlay, any key closes | [x] | [ ] | — | **FAIL** — overlay overwritten by IPC refresh. **FIX APPLIED**: render_info() guards on _web_url_visible. |
| 8 | Press `w` on Now Playing page — overlay stays visible 3+ seconds | [x] | [ ] | — | **FAIL** — same as #7. **FIX APPLIED**: _render_now_playing() and _poll_info() skip when overlay visible. |
| 9 | Replace prompt wording: "Already playing" / "Play this instead?" / "y play" | [x] | [x] | — | User suggests: ENTER = play, BACKSPACE = go back. |
| 10 | Press `y` on replace — new item plays, old session stops | [ ] | [x] | Didn't add a harness capture for this | Pass. |
| 11 | Press `n` on replace — cancel, returns to info page (not browser) | [x] | [ ] | — | **FIX APPLIED**: now returns to info. |
| 12 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [x] | — | Pass. |
| 13 | Long filenames truncated to ~40 chars + SxxExx | [x] | [x] | — | Pass. |
| 14 | Info page Progress shows live IPC position (not cached) | [x] | [x] | — | Pass. |
| 15 | Info page Progress auto-updates without cursor movement | [ ] | [ ] | Didn't add a harness capture for this; also unclear if timer-based refresh works without key events | **FAIL** — needs cursor movement. **FIX APPLIED**: added self.refresh() in poll. |
| 16 | Only one Progress line visible (no duplicate) | [x] | [ ] | — | **FIX APPLIED**: regex fixed from `Progress\s*:` to `Progress\s`. |
| 17 | Info page backspace → returns to browser | [x] | [x] | — | Pass. |
| 18 | Info → play → backspace from Now Playing → returns to info page | [x] | [x] | — | Pass. |
| 19 | Ctrl+G — mpv log works with line numbers | [x] | [x] | — | Pass. |
| 20 | MpV log scroll position indicator when scrollable | [x] | [ ] | — | User note: "it's a bar but was supposed to be textual scroll bar" — █░ doesn't render in SVG export. |

---

## Round 2 — New Re-test Requests

| # | Test | Harness | Manual | Why no harness? | Notes |
|---|------|---------|--------|-----------------|-------|
| 21 | Press Enter on replace prompt → starts playback | [ ] | [ ] | Didn't add a harness capture for this | **FIX APPLIED**: Enter now mapped to play. |
| 22 | Press Backspace on replace prompt → cancels, returns to info | [x] | [ ] | — | **FIX APPLIED**: Backspace now returns to info. |
| 23 | Press `n` on replace prompt → cancels, returns to info | [x] | [ ] | — | Same fix as #22. |
| 24 | Press `y` on replace → new item plays, old session stops | [ ] | [ ] | Didn't add a harness capture for this | |
| 25 | Replace prompt wording: "Already playing" / "Play this instead?" / "y play" | [x] | [ ] | — | Harness verified. |
| 26 | Info page Progress shows live IPC position (not cached) | [x] | [ ] | — | |
| 27 | Info page Progress auto-updates without cursor movement | [ ] | [ ] | Didn't add a harness capture for this; also unclear if timer-based refresh works without key events | **FIX APPLIED**: added self.refresh() in poll. |
| 28 | Only one Progress line visible (no duplicate) | [x] | [ ] | — | **FIX APPLIED**: regex fixed. |
| 29 | Press `w` on info page → web URL overlay, stays visible | [x] | [ ] | — | **FIX APPLIED**: render_info() guards on _web_url_visible. |
| 30 | Press `w` on Now Playing page → overlay stays visible 3+ seconds | [x] | [ ] | — | **FIX APPLIED**: _render_now_playing() and _poll_info() skip when overlay visible. |
| 31 | Press `w` → any key closes overlay | [x] | [ ] | — | |
| 32 | Press `Space` → toggles pause/play | [x] | [ ] | — | |
| 33 | Press `,` → seeks -10s | [x] | [ ] | — | |
| 34 | Press `.` → seeks +10s | [x] | [ ] | — | |
| 35 | Press `Ctrl+B` → quality cycles, flash message | [x] | [ ] | — | |
| 36 | Press `Ctrl+B` → video does NOT restart (position preserved) | [ ] | [ ] | Didn't add a harness capture for this | **FIX APPLIED**: seek back after loadfile_replace. |
| 37 | Press `Ctrl+K` → stops playback | [x] | [ ] | — | |
| 38 | Press `Ctrl+P` → playback control menu (not Textual palette) | [x] | [ ] | — | **FAIL** — Textual palette may still intercept. Needs real-keyboard test. |
| 39 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [ ] | — | |
| 40 | Long filenames truncated to ~40 chars + SxxExx | [x] | [ ] | — | |
| 41 | Bottom bar updates live with IPC position | [x] | [ ] | — | |
| 42 | Info page backspace → returns to browser | [x] | [ ] | — | |
| 43 | Info → play → backspace from Now Playing → returns to info | [x] | [ ] | — | |
| 44 | Now Playing backspace → returns to previous page | [x] | [ ] | — | |
| 45 | Ctrl+G → mpv log with line numbers | [x] | [ ] | — | |
| 46 | MpV log scroll position indicator when scrollable | [x] | [ ] | — | |
| 47 | Open app, play item → Now Playing auto-shows | [x] | [ ] | — | |

---

## Summary

**Passed (both harness & manual):** 1, 2, 3, 6, 9, 12, 13, 14, 17, 18, 19

**Fixed, needs re-test:** 4, 7, 8, 11, 16, 22, 28, 29, 30

**Still failing:** 5 (Ctrl+P Textual palette), 15/27 (info Progress auto-update)

**Harness has capture but needs manual verification:** 25, 26, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47

**Missing harness capture (should add):** 10, 15, 21, 24, 27, 36
