# Manual Re-test Checklist — 0.0.34

These items were fixed after initial manual testing. All need real-keyboard verification.

## How to use

- [ ] = not tested yet
- [x] = passed
- [ ] **FAIL** = something is wrong, add a note

---

## Playback Controls

- [ ] Open app, play an item — Now Playing page should auto-show (no Ctrl+N needed).
- [ ] Press `Space` — should toggle pause, bottom bar state should update.
- [ ] Press `,` / `.` — should seek ±10s, position should update in bottom bar.
- [ ] Press `Ctrl+B` — quality should cycle, 3-second flash message shown on Now Playing page.
- [ ] Press `Ctrl+P` — playback control menu should appear with all controls (not Textual command palette).
- [ ] Press `Ctrl+K` — should stop playback via IPC.

## Web URL Overlay

- [ ] Press `w` on info page — Jellyfin web URL overlay should appear. Any key closes it.
- [ ] Press `w` on Now Playing page — overlay should appear and **stay visible for 3+ seconds** without disappearing.

## Replace Prompt

- [ ] Play an item, navigate to another, press Enter at info — replace prompt should appear.
- [ ] Replace prompt shows "Already playing" / "Play this instead?" / "y play  n cancel" wording.
- [ ] Press `y` — new item should start playing, old Jellyfin session should be stopped.
- [ ] Press `n` — cancel, return to browser.

## Bottom Bar

- [ ] Bottom bar shows `np: <title> – <MM:SS>` format during playback (e.g. `np: Rick and Morty – S09E02 – 2:34`).
- [ ] Long filenames truncated to ~40 chars of show name + SxxExx.

## Info Page Live Progress

- [ ] While playing, open info page for the playing item — Progress line shows live IPC position (not cached Jellyfin data).
- [ ] Progress line **auto-updates** without moving cursor or pressing keys.
- [ ] Only **one** Progress line visible (no duplicate).

## Navigation

- [ ] Open info page for playing item, press q/backspace → returns to browser.
- [ ] Open info → play → backspace from Now Playing → returns to **info page** (not browser).

## MpV Log

- [ ] Press `Ctrl+G` during playback — mpv log page should still work.
- [ ] MpV log shows line numbers next to each line.
- [ ] MpV log shows scroll position indicator (█░ bar + percentage) when content is scrollable.

---

## Notes

Add any failures or observations here:

```
- 
```
