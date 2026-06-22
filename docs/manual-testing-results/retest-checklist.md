# Manual Re-test Checklist — 0.0.34

## Legend

- [x] = passed
- [ ] = not tested yet
- **FAIL** = something is wrong, add a note

## Testing

| Test | Harness | Manual |
|------|---------|--------|
| Open app, play an item — Now Playing page auto-shows | [x] | [ ] |
| Press `Space` — toggles pause, bottom bar updates | [ ] | [ ] |
| Press `,` / `.` — seeks ±10s, position updates in bottom bar | [ ] | [ ] |
| Press `Ctrl+B` — quality cycles, 3-second flash on Now Playing page | [x] | [ ] |
| Press `Ctrl+P` — playback control menu appears (not Textual palette) | [ ] | [ ] |
| Press `Ctrl+K` — stops playback via IPC | [ ] | [ ] |
| Press `w` on info page — web URL overlay appears, any key closes | [x] | [ ] |
| Press `w` on Now Playing page — overlay stays visible 3+ seconds | [ ] | [ ] |
| Replace prompt shows "Already playing" / "Play this instead?" / "y play" | [x] | [ ] |
| Press `y` on replace — new item plays, old session stops | [ ] | [ ] |
| Press `n` on replace — cancel, returns to browser | [ ] | [ ] |
| Bottom bar shows `np: <title> – <MM:SS>` format | [ ] | [ ] |
| Long filenames truncated to ~40 chars + SxxExx | [ ] | [ ] |
| Info page Progress shows live IPC position (not cached) | [x] | [ ] |
| Info page Progress auto-updates without cursor movement | [ ] | [ ] |
| Only one Progress line visible (no duplicate) | [x] | [ ] |
| Info page backspace → returns to browser | [ ] | [ ] |
| Info → play → backspace from Now Playing → returns to info page | [ ] | [ ] |
| Ctrl+G — mpv log works with line numbers | [x] | [ ] |
| MpV log scroll position indicator (█░ bar + %) when scrollable | [x] | [ ] |

## Notes

Add any failures or observations here:

```
- 
```
