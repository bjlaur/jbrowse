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

---

## New Re-test Requests

### Replace Prompt

- [ ] Press Enter on replace prompt → starts playback (same as `y`)
- [ ] Press Backspace on replace prompt → cancels and returns to info page
- [ ] Press `n` on replace prompt → cancels and returns to info page (not browser)
- [ ] Press `y` on replace prompt → starts new playback, old session stops
- [ ] Replace prompt shows "Already playing" / "Play this instead?" / "y play  n cancel"

**Notes:**

---

### Info Page Live Progress

- [ ] Open info page for a currently playing item → Progress line shows live IPC position
- [ ] Progress line updates automatically every second without moving cursor
- [ ] Only one Progress line visible (no duplicate)
- [ ] Progress line shows correct position from IPC (e.g. `Progress: 2:34 / 22:10`)

**Notes:**

---

### Web URL Overlay

- [ ] Press `w` on info page → overlay shows Jellyfin web URL
- [ ] Press `w` on info page → overlay stays visible (not overwritten by IPC refresh)
- [ ] Press any key → overlay closes
- [ ] Press `w` on Now Playing page → overlay shows Jellyfin web URL
- [ ] Press `w` on Now Playing page → overlay stays visible for 3+ seconds

**Notes:**

---

### Playback Controls

- [ ] Press `Space` → toggles pause/play, bottom bar updates
- [ ] Press `,` → seeks -10s, position updates in bottom bar
- [ ] Press `.` → seeks +10s, position updates in bottom bar
- [ ] Press `Ctrl+B` → quality cycles, 3-second flash message on Now Playing page
- [ ] Press `Ctrl+B` → video does NOT restart (seamless transition, position preserved)
- [ ] Press `Ctrl+K` → stops playback via IPC
- [ ] Press `Ctrl+P` → playback control menu appears (not Textual command palette)

**Notes:**

---

### Bottom Bar

- [ ] Bottom bar shows `np: <title> – <MM:SS>` format during playback
- [ ] Long filenames truncated to ~40 chars of show name + SxxExx
- [ ] Bottom bar updates live with IPC position

**Notes:**

---

### Navigation

- [ ] Info page backspace → returns to browser
- [ ] Info → play → backspace from Now Playing → returns to info page
- [ ] Now Playing backspace → returns to previous page (info or browser)

**Notes:**

---

### MpV Log

- [ ] Press `Ctrl+G` during playback → mpv log page works
- [ ] MpV log shows line numbers next to each line
- [ ] MpV log shows scroll position indicator when content is scrollable

**Notes:**

---

### General

- [ ] Open app, play an item → Now Playing page auto-shows (no Ctrl+N needed)
- [ ] Ctrl+G — mpv log works with line numbers

**Notes:**
