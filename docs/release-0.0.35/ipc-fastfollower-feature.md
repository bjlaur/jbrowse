# IPC Fast Follower — 0.0.35

Small fixes and polish deferred from 0.0.34. Quick wins that don't require much discussion.

---

## From Retest Checklist (Round 4 — user said "next release")

### Ctrl+P Textual Palette Verification
**Source**: Retest #5 — user said "don't fix this one, just add to known issues for next release"

**Issue**: Can't fully confirm Textual palette is suppressed without physical keyboard. Harness passes but manual test was FAIL.

**Action**: Verify with real keyboard that `ENABLE_COMMAND_PALETTE = False` actually prevents Textual palette. If it doesn't work, investigate further.

---

### Info Progress Auto-Update Visibility
**Source**: Retest #61 — user said "todo - take care of in next release"

**Issue**: Harness passes but manual test fails. Timer-based refresh may not be visible without cursor movement.

**Action**: Investigate why manual test sees no auto-update. May need:
- Longer poll interval
- A visual indicator (blinking cursor, timestamp)
- Confirming `self.refresh()` actually triggers a screen redraw

**Files**: `jbrowse.py` (`_poll_info()`)

---

### Long Filename Truncation Testing
**Source**: Retest #66 — user said "UHM.. I asked you for how to test this. did you ever tell me?"

**Issue**: User couldn't figure out how to test truncation. No fixture data with real long filenames.

**Action**: Add items with deliberately long filenames to fixture data. Verify bottom bar truncation shows `…` correctly.

Example long filename: `Rick.and.Morty.S09E02.Ricks.Days.Seven.Nights.1080p.AMZN.WEB-DL.DDP5.1.H.264-Kitsune.mkv` → should show as `Rick and Morty – S09E02` in bottom bar.

**Files**: `tools/fake_cache_data.json.zst` (add long-name test items), possibly `jbrowse.py` (truncation logic review)

---

### Ctrl+B Position Preserved (Manual Test Verification)
**Source**: Retest #60 — manual test was skipped

**Issue**: User was frustrated — "the hell you can't" verify position preservation. The `--real --real-mpv-bitrate` automated test covers this, but manual test was never done.

**Action**: Verify the existing `--real --real-mpv-bitrate` test adequately covers position preservation. If confident, mark as done. Otherwise write a simpler manual-verifiable test.

---

## From TODO.md (Small Fixes, No Discussion Needed)

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

## Deferred (Need User Input — NOT Fast Follower)

These need discussion with the user before implementing:

- **Replace prompt wording** (#25/#59) — User doesn't like current phrasing but hasn't decided on new wording. Panel title "Replace Playback" could also be improved.
