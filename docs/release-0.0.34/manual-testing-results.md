# IPC Manual Testing Results

## Initial Test Results

- [x] Press `Space` — should toggle pause, bottom bar state should update. -- works
- [x] Press `,` / `.` — should seek ±10s, position should update in bottom bar.
- [x] Press `Ctrl+B` — quality should cycle, brief status message shown. -- **Needs manual test**: code adds 3-second flash message on Now Playing page; can't verify timing in harness.
- [x] Press `Ctrl+P` — playback control menu should appear with all controls. -- **Needs manual test**: moved `use_command_palette = False` to class level; must verify with real keyboard that Textual palette no longer appears.
- [x] Play an item, navigate to another, press Enter at info — replace prompt should appear. -- **Harness verified**: wording changed to "Already playing" / "Play this instead?" / "y play  n cancel".
- [x] Press `y` — new item should start playing, old Jellyfin session should be stopped. -- works
- [x] Press `Ctrl+G` during playback — mpv log page should still work. -- **Harness verified**: line numbers + scroll position indicator added. Static capture passes.
- [x] Press `Ctrl+K` — should stop playback via IPC. -- works

## Re-test Results (items fixed after initial manual testing)

- [x] **Auto-show Now Playing**: Play any item → Now Playing page appears automatically. q/backspace → returns to previous page (info or browser). -- **Needs manual test**: code uses `self.previous_page` now; must verify navigation from info → now playing → backspace returns to info.
- [x] **Truncated bottom bar titles**: Long filenames show as `Rick and Morty – S09E02` in the bottom bar. -- **Needs manual test**: increased to 40 chars, en dash separator, `np:` prefix; must verify in live terminal during playback.
- [x] **Web URL hotkey (`w`)**: On info page or Now Playing page, press `w` → overlay shows Jellyfin web URL. Any key closes it. -- **Needs manual test**: poll timer skips re-rendering when overlay visible; must verify overlay stays visible for 3+ seconds on Now Playing page.
- [x] **Live IPC progress on info page**: While playing, open the info page for the playing item → Progress line shows live position from IPC, auto-updates. -- **Needs manual test**: fixed regex matching for Progress line; added 1-second auto-update poll; must verify progress updates without cursor movement.
