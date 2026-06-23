# IPC Fast Follower — 0.0.35

Small fixes and polish that don't require much discussion. Quick wins after the 0.0.34 release.

---

## Small UI Fixes

### Better Help Text / Key Map Cleanup
**Effort**: Small (~50 lines reorganization)

**Current**: Flat list of all hotkeys in one block.
**Goal**: Sectioned list — Browsing, Search, Info, Playback, Themes, App.

Also: `Ctrl+Shift+X` reverse theme cycling may not be reliably distinguishable from `Ctrl+X` in terminals. Consider alternatives.

**Files**: `jbrowse.py` (`render_help()` only)

---

### Bottom Bar Progress Bar
**Effort**: Small

**Current**: Bottom bar shows text only: `np: <title> – <MM:SS>`.
**Goal**: Add a compact visual `█░` progress bar to the bottom status bar during playback.

Now Playing page already has a full bar; this would be a compact version for the browser bottom bar.

**Files**: `jbrowse.py` (`update_bottom_status()` or `bottom_status_text()`)

---

### Info Progress Auto-Update Visibility
**Effort**: Small

**Current**: Info page Progress line has a 1-second auto-update poll with `self.refresh()`, but it may not be visibly obvious.
**Goal**: Investigate whether the timer-based refresh is actually visible to the user. May need:
- A longer poll interval
- A visual indicator (blinking cursor, timestamp)
- Confirming the refresh actually triggers a screen redraw

**Files**: `jbrowse.py` (info page poll logic)

---

### Long Filename Truncation Testing
**Effort**: Small (fixture data + verification)

**Current**: User couldn't figure out how to test truncation. No fixture data with real long filenames.
**Goal**: Add a few items with deliberately long filenames to the fixture data. Verify bottom bar truncation shows `…` correctly.

**Files**: `tools/fake_cache_data.json.zstr` (add long-name test items), possibly `jbrowse.py` (truncation logic review)

---

## Known Issues to Revisit (Need User Input)

These are deferred — they need discussion with the user before implementing:

- **Replace prompt wording** — User doesn't like current phrasing but hasn't decided on new wording. Panel title "Replace Playback" could also be improved.
- **Ctrl+P Textual palette** — Can't fully confirm Textual palette is suppressed without physical keyboard. Verify with real keyboard next release.
- **Ctrl+B position preserved (manual test)** — Was skipped. Verify the existing `--real --real-mpv-bitrate` test covers this adequately.
