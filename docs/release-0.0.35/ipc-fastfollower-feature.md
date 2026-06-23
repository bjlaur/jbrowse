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

Now Playing page already has a full progress bar; this would be a compact version for the browser bottom bar.

**Files**: `jbrowse.py` (`update_bottom_status()` or `bottom_status_text()`)

---

## Known Issues to Revisit (Need User Input)

These are deferred — they need discussion with the user before implementing:

- **Replace prompt wording** — User doesn't like current phrasing but hasn't decided on new wording
- **Info Progress auto-update** — Timer-based refresh may not be visible without cursor movement; needs investigation
- **Ctrl+P Textual palette** — Can't fully verify suppression without real keyboard
