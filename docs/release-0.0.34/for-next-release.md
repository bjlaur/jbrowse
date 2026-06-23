# For-Next-Release — Known Issues Deferred from 0.0.34

These items are functional but have known rough edges. They don't block the release but should be addressed in the next cycle.

---

## UI Polish

### #5 — Ctrl+P Textual palette
- **Status:** Harness passes, manual can't verify without real keyboard
- **Issue:** Can't fully confirm Textual palette is suppressed without physical keyboard
- **Action:** Add to known issues list; verify with real keyboard next release

### #25 — Replace prompt wording
- **Status:** Passes but user doesn't like current formatting
- **Current:** "Already playing" / "Play this instead?" / "Enter play  Backspace cancel"
- **Action:** Revisit wording and panel title in next release

### #46 — MpV log scroll indicator
- **Status:** ✅ Fixed — changed `█░` block characters to `[####----] 42%` text format
- **Action:** Done

### #59 — Replace prompt text formatting
- **Status:** Passes but user doesn't love the formatting
- **Action:** Same as #25 — revisit in next release

### #65 — Bottom bar format
- **Status:** ✅ Fixed — poll timer now calls `update_bottom_status()` which respects page context (subtitle status on info page, np: status elsewhere)
- **Action:** Done

### #67 — Help key binding
- **Status:** ✅ Fixed — changed from `Ctrl+L`/`?` to `Ctrl+H`
- **Action:** Done

### #68 — `?` key help
- **Status:** ✅ Fixed — removed `?` binding entirely
- **Action:** Done

---

## Features To Revisit

### #60 — Ctrl+B position preserved (manual test)
- **Status:** Manual test skipped (user frustrated — other agent wrote the test)
- **Action:** Verify the existing `--real --real-mpv-bitrate` test covers this adequately

### #61 — Info Progress auto-update
- **Status:** Harness passes, manual fails
- **Issue:** Timer-based refresh may not be visible without cursor movement
- **Action:** Investigate why manual test sees no auto-update; may need longer poll interval or visual indicator

### #66 — Long filename truncation
- **Status:** User couldn't figure out how to test
- **Action:** Provide a way to test with real long filenames; may need fixture data with long names

---

## New Issue (user-added)

### mpv-close → info page
- **Status:** ✅ Fixed — `poll_playback_status()` now returns to `previous_page` (info) instead of hardcoded browser
- **Action:** Done

---

## Summary

| Category | Count | Items |
|----------|-------|-------|
| UI polish (wording/formatting) | 3 | #25, #59, #65 |
| Key binding cleanup | 2 | #67, #68 |
| Scroll indicator redesign | 1 | #46 |
| Needs real-keyboard verify | 1 | #5 |
| Timer/refresh issues | 2 | #61, #65 |
| New feature | 1 | mpv-close → info |
| Test coverage | 2 | #60, #66 |
