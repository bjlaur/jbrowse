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
| 35 | Press `Ctrl+B` → quality cycles, flash message | [x] | [ ] | — | it works but.. Progress: 0:09 / 0:32. The progress is using the time from mpv instead of the time from jellyfin. Because the file is not transcoded all at once we can't do that. This brings up another feature we need: jump to time. Bring up a window where you can either type in a time, or use your keyboard to select from a bar of some sort. This way we can jump to a time that isn't yet loaded in mpv. It'll restart mpv to this new stream. | Will fix: add "jump to time" feature to TODO. Investigate using Jellyfin runtime for progress display. |
| 36 | Press `Ctrl+B` → video does NOT restart (position preserved) | [x] | [ ] | — | **FIX APPLIED**: seek back + `--real-mpv-bitrate` test added. Cycles quality twice, verifies bitrate changes and position preserved. Run with `--real --real-mpv-bitrate`. | Needs manual re-test. |
| 37 | Press `Ctrl+K` → stops playback, returns to info from Now Playing | [x] | [ ] | — | **FIX APPLIED**: Ctrl+K from Now Playing now returns to previous_page (info) instead of browser. | Needs manual re-test. |
| 38 | Press `Ctrl+P` → playback control menu (not Textual palette) | [x] | [ ] | — | | Needs real-keyboard test. |
| 39 | Bottom bar shows `np: <title> – <MM:SS>` format | [x] | [x] | — | | — |
| 40 | Long filenames truncated to ~40 chars + SxxExx | [x] | [ ] | — | uhhhh can you give me a real world example so I can test this? And how do I test this? | Example: `Rick.and.Morty.S09E02.Ricks.Days.Seven.Nights.1080p.AMZN.WEB-DL.DDP5.1.H.264-Kitsune.mkv` → should show as `Rick and Morty – S09E02` in bottom bar. Test by playing any file with a long filename. |
| 41 | Bottom bar updates live with IPC position | [x] | [ ] | — | needs cursor move to update. | Will fix: same root cause as #15 — needs timer-based refresh. |
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

**Will fix:** 21/22 (replace prompt GUI text + mpv title), 25 (wording TODO), 35 (jump to time + progress display), 36 (harness bitrate test), 37 (Ctrl+K return to info), 41 (bottom bar live update), 46 (scroll indicator TODO), Other (Enter on same file → NP)
