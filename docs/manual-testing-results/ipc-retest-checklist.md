# IPC Re-test Checklist — 0.0.34

## Legend

- [x] = passed
- [ ] = not tested yet
- **FAIL** = broken, needs fix

---

| # | Test | Harness | Manual | Notes |
|---|------|---------|--------|-------|
| 1 | Open app, play an item — Now Playing page auto-shows | [x] | [x] | |
| 2 | Press `Space` — toggles pause, bottom bar updates | [x] | [x] | |
| 3 | Press `,` / `.` — seeks ±10s, position updates in bottom bar | [x] | [x] | |
| 4 | Press `Ctrl+B` — quality cycles, 3-second flash on Now Playing page | [x] | [ ] | **Needs server log check** — did it actually transcode? Video restarts when quality changes (should be seamless). **FIX APPLIED**: now seeks back to saved position after loadfile_replace. Needs re-test. |
| 5 | Press `Ctrl+P` — playback control menu appears (not Textual palette) | [x] | [ ] | **FAIL** — Textual command palette still appears instead of playback control menu. Needs real-keyboard test after fix. |
| 6 | Press `Ctrl+K` — stops playback via IPC | [x] | [x] | Pass. |
| 7 | Press `w` on info page — web URL overlay appears, any key closes | [x] | [ ] | **FAIL** — overlay gets overwritten by IPC refresh. **FIX APPLIED**: render_info() now checks _web_url_visible. Needs re-test. |
| 8 | Press `w` on Now Playing page — overlay stays visible 3+ seconds | [x] | [ ] | **FAIL** — same as above. **FIX APPLIED**: _render_now_playing() and _poll_info() now skip when _web_url_visible. Needs re-test. |
| 9 | Replace prompt shows "Already playing" / "Play this instead?" / "y play" | [x] | [x] | User suggests: ENTER = play, BACKSPACE = go back. |
| 10 | Press `y` on replace — new item plays, old session stops | [ ] | [x] | Pass. |
| 11 | Press `n` on replace — cancel, returns to info page (not browser) | [x] | [ ] | **FAIL** — was returning to browser. **FIX APPLIED**: now returns to info page. Needs re-test. |
| 12 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [x] | Pass. |
| 13 | Long filenames truncated to ~40 chars + SxxExx | [x] | [x] | Pass. |
| 14 | Info page Progress shows live IPC position (not cached) | [x] | [x] | Pass. |
| 15 | Info page Progress auto-updates without cursor movement | [ ] | [ ] | **FAIL** — still requires cursor movement to see update. Poll timer may not be refreshing display properly. Needs investigation. |
| 16 | Only one Progress line visible (no duplicate) | [x] | [ ] | **FAIL** — duplicate Progress line still appears. Harness passed because fake data doesn't trigger the bug. **FIX APPLIED**: changed regex from `Progress\s*:` to `Progress\s`. Needs re-test. |
| 17 | Info page backspace → returns to browser | [x] | [x] | Pass. |
| 18 | Info → play → backspace from Now Playing → returns to info page | [x] | [x] | Pass. |
| 19 | Ctrl+G — mpv log works with line numbers | [x] | [x] | Pass. |
| 20 | MpV log scroll position indicator when scrollable | [x] | [ ] | User note: "it's a bar but was supposed to be textual actual scroll bar" — the █░ bar renders in terminal but not in SVG export. May need a text-based indicator like `line 5/50` instead. |

---

## Summary

**Passed (both harness & manual):** 1, 2, 3, 6, 9, 10, 12, 13, 14, 17, 18, 19

**Fixed in this session, needs re-test:** 4 (seek back after quality change), 7 (web URL overlay on info), 8 (web URL overlay on Now Playing), 11 (replace n → info), 16 (duplicate Progress regex)

**Still failing, needs investigation:** 5 (Ctrl+P Textual palette), 15 (info Progress auto-update), 20 (scroll bar text format)

**Harness-only (can't test manually yet):** All harness captures pass (28/28).
