# IPC Re-test Checklist — 0.0.34

## Legend

- [x] = passed
- [ ] = not tested yet
- **FAIL** = broken, needs fix

---

## Round 1 — Initial Fixes

| # | Test | Harness | Manual | Why no harness? | Dev notes |
|---|------|---------|--------|-----------------|-----------|
| 1 | Open app, play an item — Now Playing page auto-shows | [x] | [x] | — | |
| 2 | Press `Space` — toggles pause, bottom bar updates | [x] | [x] | — | |
| 3 | Press `,` / `.` — seeks ±10s, position updates in bottom bar | [x] | [x] | — | |
| 4 | Press `Ctrl+B` — quality cycles, 3-second flash on Now Playing page | [x] | [ ] | — | **Needs server log check** — did it actually transcode? Video restarts (should be seamless). **FIX APPLIED**: seek back after loadfile_replace. |
| 5 | Press `Ctrl+P` — playback control menu appears (not Textual palette) | [x] | [ ] | — | **FAIL** — Textual palette still appears. Needs real-keyboard test. |
| 6 | Press `Ctrl+K` — stops playback via IPC | [x] | [x] | — | Pass. |
| 7 | Press `w` on info page — web URL overlay, any key closes | [x] | [ ] | — | **FAIL** — overlay overwritten by IPC refresh. **FIX APPLIED**: render_info() guards on _web_url_visible. |
| 8 | Press `w` on Now Playing page — overlay stays visible 3+ seconds | [x] | [ ] | — | **FAIL** — same as #7. **FIX APPLIED**: _render_now_playing() and _poll_info() skip when overlay visible. |
| 9 | Replace prompt wording: "Already playing" / "Play this instead?" / "Enter play  Backspace cancel" | [x] | [x] | — | Panel title: "Replace Playback". **FIX APPLIED**: text and title updated. |
| 10 | Press `y` on replace — new item plays, old session stops | [ ] | [x] | Didn't add a harness capture | Pass. |
| 11 | Press `n` on replace — cancel, returns to info page (not browser) | [x] | [ ] | — | **FIX APPLIED**: now returns to info. |
| 12 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [x] | — | Pass. |
| 13 | Long filenames truncated to ~40 chars + SxxExx | [x] | [x] | — | Pass. |
| 14 | Info page Progress shows live IPC position (not cached) | [x] | [x] | — | Pass. |
| 15 | Info page Progress auto-updates without cursor movement | [ ] | [ ] | Didn't add a harness capture; timer-based refresh can't be verified in static SVG | **FAIL** — needs cursor movement. **FIX APPLIED**: added self.refresh() in poll. |
| 16 | Only one Progress line visible (no duplicate) | [x] | [ ] | — | **FIX APPLIED**: regex fixed from `Progress\s*:` to `Progress\s`. |
| 17 | Info page backspace → returns to browser | [x] | [x] | — | Pass. |
| 18 | Info → play → backspace from Now Playing → returns to info page | [x] | [x] | — | Pass. |
| 19 | Ctrl+G — mpv log works with line numbers | [x] | [x] | — | Pass. |
| 20 | MpV log scroll position indicator when scrollable | [x] | [ ] | — | User note: "it's a bar but was supposed to be textual scroll bar" — █░ doesn't render in SVG export. |

---

## Round 2 — New Re-test Requests

| # | Test | Harness | Manual | Why no harness? | Dev notes | Agent notes |
|---|------|---------|--------|-----------------|-----------|-------------|
| 21 | Press Enter on replace prompt → starts playback | [x] | [ ] | — | **FIX APPLIED**: GUI text now shows "Enter play  Backspace cancel", panel title "Replace Playback". | Needs re-test. |
| 22 | Press Backspace on replace prompt → cancels, returns to info | [x] | [ ] | — | **FIX APPLIED**: Same as #21. | Needs re-test. |
| 23 | Press `n` on replace prompt → cancels, returns to info | [x] | [x] | — | Pass (although I did backspace) | — |
| 24 | Press `y` on replace → new item plays, old session stops | [ ] | [x] | Didn't add a harness capture | Pass (although I did enter) | — |
| 25 | Replace prompt wording: "Already playing" / "Play this instead?" / "Enter play  Backspace cancel" | [x] | [ ] | — | **FIX APPLIED**: Updated to "Enter play  Backspace cancel". | Needs re-test. |
| 26 | Info page Progress shows live IPC position (not cached) | [x] | [ ] | — | | — |
| 27 | Info page Progress auto-updates without cursor movement | [x] | [ ] | — | **FIX APPLIED**: added self.refresh() in poll. | Needs re-test. |
| 28 | Only one Progress line visible (no duplicate) | [x] | [x] | — | **FIX APPLIED**: regex fixed. | — |
| 29 | Press `w` on info page → web URL overlay, stays visible | [x] | [ ] | — | **FIX APPLIED**: render_info() guards on _web_url_visible. | Needs re-test. |
| 30 | Press `w` on Now Playing page → overlay stays visible 3+ seconds | [x] | [x] | — | **FIX APPLIED**: _render_now_playing() and _poll_info() skip when overlay visible. | — |
| 31 | Press `w` → any key closes overlay | [x] | [x] | — | idk, I just did backspace that's good enough. | — |
| 32 | Press `Space` → toggles pause/play | [x] | [ ] | — | I already tested.. why am I being asked to test again. | Skip — carried over from round 1, already passed. |
| 33 | Press `,` → seeks -10s | [x] | [ ] | — | I already tested.. why am I being asked to test again. | Skip — carried over from round 1, already passed. |
| 34 | Press `.` → seeks +10s | [x] | [ ] | — | I already tested.. why am I being asked to test again. | Skip — carried over from round 1, already passed. |
| 35 | Press `Ctrl+B` → quality cycles, flash message | [x] | [x] | — | it works but.. Progress: 0:09 / 0:32. The progress is using the time from mpv instead of the time from jellyfin. Jump to time feature now exists (press `j` on Now Playing page). | **FIXED**: Jump to time overlay added with real IPC test. Progress display still uses mpv time-pos. | **FIXED**: Jump-to-time overlay, `j` key on Now Playing page. `--real-mpv-jump` test passes. |
| 36 | Press `Ctrl+B` → video does NOT restart (position preserved) | [x] | [x] | — | **FIX APPLIED**: seek back + `--real-mpv-bitrate` test added. Cycles quality twice, verifies bitrate changes and position preserved. Run with `--real --real-mpv-bitrate`. | **FIXED**: `--real-mpv-bitrate` rewritten with hybrid approach. Position preserved across all 3 quality cycles (direct→40mbps→20mbps). |
| 37 | Press `Ctrl+K` → stops playback, returns to info from Now Playing | [x] | [x] | — | **FIX APPLIED**: Ctrl+K from Now Playing now returns to previous_page (info) instead of browser. | **FIXED**: Ctrl+K stops playback and returns to info page. |
| 38 | Press `Ctrl+P` → playback control menu (not Textual palette) | [x] | [ ] | — | | Needs real-keyboard test. |
| 39 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [x] | — | | — |
| 40 | Long filenames truncated to ~40 chars + SxxExx | [x] | [ ] | — | uhhhh can you give me a real world example so I can test this? And how do I test this? | Example: `Rick.and.Morty.S09E02.Ricks.Days.Seven.Nights.1080p.AMZN.WEB-DL.DDP5.1.H.264-Kitsune.mkv` → should show as `Rick and Morty – S09E02` in bottom bar. Test by playing any file with a long filename. |
| 41 | Bottom bar updates live with IPC position | [x] | [x] | — | needs cursor move to update. | **FIXED**: Added bottom bar poll timer that updates widget every second during playback. | **FIXED**: Bottom bar poll timer updates widget every second. |
| 42 | Info page backspace → returns to browser | [x] | [x] | — | | — |
| 43 | Info → play → backspace from Now Playing → returns to info | [x] | [x] | — | | — |
| 44 | Now Playing backspace → returns to previous page | [x] | [x] | — | | — |
| 45 | Ctrl+G → mpv log with line numbers | [x] | [ ] | — | why am I being asked to retest? | Skip — carried over from round 1, already passed. |
| 46 | MpV log scroll position indicator when scrollable | [x] | [ ] | — | add to todo to look into a better solution. | Will fix: add to TODO — █░ bar doesn't render in SVG, needs text-based indicator. |
| 47 | Open app, play item → Now Playing auto-shows | [x] | [x] | — | | — |

---

## Other Issues

- **Enter on same file**: If you press Enter on the same file you're already playing, it should just take you back to Now Playing page (not show replace prompt). **FIX APPLIED**: `start_playback()` now checks if item ID matches current and opens Now Playing directly.

---

## Round 3 — New Retest Requests

| #   | Test                                                               | Harness | Manual   | Why no harness?                 | Dev notes                                         | Agent notes                                                                                                                  |
| --- | ------------------------------------------------------------------ | ------- | -------- | ------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 48  | Press Enter on same file → opens Now Playing (no replace prompt)   | [ ]     | [x]      | Didn't add a harness capture    |                                                   | **FIX APPLIED**: same-item check in `start_playback()`. Needs re-test.                                                       |
| 49  | Ctrl+K from Now Playing → returns to info page                     | [ ]     | [x]      | Didn't add a harness capture    |                                                   | **FIX APPLIED**: Ctrl+K handler now checks `self.page == "now_playing"` and returns to `previous_page`. Needs re-test.       |
| 50  | Replace prompt text shows "Enter → replace" / "Backspace → cancel" | [x]     | [x]      | —                               |                                                   | **FIX APPLIED**: updated text format. Harness capture updated to match. Needs re-test.                                       |
| 51  | Ctrl+B bitrate cycles through presets                              | [x]     | [x]      | —                               | **FIXED**: `--real-mpv-bitrate` passes. Hybrid approach: start playback before Textual harness. | **FIXED**: 3 cycles verified (direct→40mbps→20mbps). Position preserved. |
| 52  | Ctrl+B quality change preserves playback position                  | [x]     | [x]      | —                               | **FIXED**: position check added to bitrate test. Video does NOT restart. | **FIXED**: 20→20→20 seek test also passes. |
| 53  | Bottom bar updates live without cursor movement                    | [x]     | [x]      | —                               |                                                   | **FIX APPLIED**: added `_start_bottom_bar_poll()` timer. Needs re-test.                                                      |
| 54  | Jump-to-time overlay (`j` on Now Playing)                         | [x]     | [x]      | —                               |                                                   | **FIX APPLIED**: jump-to-time overlay with IPC seek. Needs re-test.                                                          |
| 55  | Jump-to-time `--real-mpv-jump` test passes                        | [x]     | [x]      | —                               | **FIXED**: waits for mpv to start playing before seeking. Jumps to 30s and 60s verified. | **FIXED**: both jumps verified via IPC. |

---

## Round 4 — Real IPC Test Fixes

| #   | Test                                                               | Harness | Manual   | Why no harness?                 | Dev notes                                         | Agent notes                                                                                                                  |
| --- | ------------------------------------------------------------------ | ------- | -------- | ------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 56  | Run `--real --real-mpv-bitrate` — bitrate cycles pass             | [x]     | [ ]      | Needs real mpv + Jellyfin       | **FIXED**: hybrid approach — start playback via `start_background()` before Textual harness. | Passes. Quality cycles direct→40mbps→20mbps, position preserved. Run with `--real --real-mpv-bitrate --play-duration 5`.      |
| 57  | Run `--real --real-mpv-jump` — seek to time works                 | [x]     | [ ]      | Needs real mpv + Jellyfin       | **FIXED**: wait for mpv to start playing before seeking. Increased timeouts. | Passes. Jumps to 30s and 60s verified via IPC. Run with `--real --real-mpv-jump --play-duration 5`.                          |
| 58  | Quality change does NOT restart video (position preserved)         | [x]     | [ ]      | Needs real mpv + Jellyfin       | **FIXED**: added position preservation check in bitrate test. 20→20→20 seek test. | Passes. Position stays within 50% of pre-cycle value after each quality change.                                              |

---

## Screenshot

```
                          ╭─────────── Already Playing ───────────╮
                          │                                       │
                          │  Already playing                      │
                          │                                       │
                          │  Euphoria - S03E08 - In God We Trust  │
                          │                                       │
                          │  Play this instead?                   │
                          │                                       │
                          │  Euphoria - S03E08 - In God We Trust  │
                          │                                       │
                          │  y play  n cancel                     │
                          │                                       │
                          ╰───────────────────────────────────────╯
```

---

## Summary

**Passed (both harness & manual):** 1, 2, 3, 6, 9, 12, 13, 14, 17, 18, 19

**Fixed, needs re-test:** 4, 7, 8, 11, 16, 22, 28, 29, 30

**Still failing:** 5 (Ctrl+P Textual palette), 15/27 (info Progress auto-update)

**Skip (already tested in round 1):** 32, 33, 34, 45

**Fixed in this branch:** 21/22 (replace prompt GUI text), 35 (jump to time feature + real IPC test), 37 (Ctrl+K return to info), 41 (bottom bar poll timer), Other (Enter on same file → NP)

**Agent 2 re-test results (round 2):** 35 [x] jump-to-time works, 37 [x] Ctrl+K returns to info, 41 [x] bottom bar live updates, Other [x] Enter on same file → NP

**Fixed in real-mpv-bitrate-fix branch:** 36 (bitrate test rewritten with hybrid approach, position preserved), 51 (bitrate cycles verified), 52 (position preservation verified), 55 (jump test fixed)

**Round 4 retest requests (Agent 1):** 56 (Ctrl+P playback control), 57 (Ctrl+K → info), 58 (Enter same file → NP), 59 (replace prompt text), 60 (Ctrl+B position preserved), 61 (info Progress auto-update), 62 (duplicate Progress line), 63 (web URL on info), 64 (web URL on Now Playing), 65 (bottom bar format), 66 (long filename truncation), 67 (F1 no palette), 68 (? help key)

**Still needs work:** 25 (wording revision), 46 (scroll indicator redesign)

---

## Round 4 — Agent 1 Additional Fixes

| # | Test | Harness | Manual | Why no harness? | Agent notes |
|---|------|---------|--------|-----------------|-------------|
| 56 | Press `Ctrl+P` → playback control menu (not Textual palette) | [x] | [ ] | — | **FIX APPLIED**: Changed `use_command_palette` to `ENABLE_COMMAND_PALETTE = False` (correct Textual API). `ctrl-p-from-browser` harness capture verifies. Needs real-keyboard test. |
| 57 | Ctrl+K from Now Playing → returns to info page | [ ] | [ ] | Didn't add a harness capture for this specific flow | **FIX APPLIED**: Ctrl+K handler now checks `self.page == "now_playing"` and returns to `previous_page`. |
| 58 | Enter on same file → opens Now Playing (no replace prompt) | [ ] | [ ] | Didn't add a harness capture for this | **FIX APPLIED**: `start_playback()` checks if item ID matches current and opens Now Playing directly. |
| 59 | Replace prompt text shows "Enter → replace" / "Backspace → cancel" | [x] | [ ] | — | **FIX APPLIED**: Updated `_render_replace_prompt()` text and panel title to "Replace Playback". |
| 60 | Ctrl+B quality change preserves playback position | [ ] | [ ] | Can't verify position preservation with fake IPC | **FIX APPLIED**: seek-back delay increased from 0.5s to 1.0s. Needs `--real --real-mpv-bitrate` to verify. |
| 61 | Info page Progress auto-updates without cursor movement | [x] | [ ] | — | **FIX APPLIED**: Added `self.refresh()` in `_poll_info()`. `info-progress-auto-update` capture verifies. |
| 62 | Only one Progress line visible (no duplicate) | [x] | [ ] | — | **FIX APPLIED**: Changed regex from `Progress\s*:` to `Progress\s` (add_kv format has no colon). |
| 63 | Web URL overlay on info page stays visible (not overwritten by IPC refresh) | [x] | [ ] | — | **FIX APPLIED**: `render_info()` now guards on `_web_url_visible`. |
| 64 | Web URL overlay on Now Playing page stays visible 3+ seconds | [x] | [ ] | — | **FIX APPLIED**: `_render_now_playing()` and `_poll_info()` skip when `_web_url_visible`. |
| 65 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [ ] | — | **FIX APPLIED**: Changed from "playing:"/"paused:" to "np:" prefix. |
| 66 | Long filenames truncated to ~40 chars + SxxExx | [x] | [ ] | — | **FIX APPLIED**: Increased from 10 to 40 char limit. |
| 67 | F1 key does NOT open Textual command palette | [ ] | [ ] | Can't test in harness (no real keyboard) | **FIX APPLIED**: Removed F1 from help key binding. Use `Ctrl+L` or `?` instead. |
| 68 | `?` key opens help overlay | [x] | [ ] | — | **FIX APPLIED**: `?` character triggers help. `help` capture uses `?` key. |
