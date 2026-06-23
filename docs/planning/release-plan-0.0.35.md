# Next Release Plan — Post-IPC Features (0.0.35)

## Context
IPC feature branch (0.0.34) is nearly complete. The other agent is fixing `--real-mpv-bitrate` test issues. This plan covers the next release (0.0.35) with features that are independent of the IPC work.

## Release Candidates (Prioritized)

### 1. Replace Prompt Wording (Quick Fix — User Requested)
**Priority**: HIGH (user explicitly asked)
**Effort**: Small

**Current**: "Already playing" / "Play this instead?" / "Enter → replace" / "Backspace → cancel"
**Problem**: User doesn't like the wording. Too verbose.

**Proposed approaches**:
- Minimal: Just show the two items and "Enter replace  /  Backspace cancel"
- Medium: Show current item title, new item title, and compact action labels
- Full: Redesign the entire overlay with a cleaner layout

**Files**: `jbrowse.py` (`_render_replace_prompt` method only), `tools/svg_screenshot_poc.py` (update expected text)

---

### 2. Audio Picker (Natural Next Feature)
**Priority**: HIGH (natural progression from subtitle picker)
**Effort**: Medium (~150 lines new code)

**What**: Audio track selection overlay, mirroring subtitle picker UI
**Hotkey**: `a` for audio, `s` for subtitles

**Implementation**:
1. Create `open_audio_picker()` — mirror `open_subtitle_picker()` pattern
2. Use `PlaybackManager.ipc_get_property("track-list")` for track enumeration
3. Render overlay: language, codec, channels, default flag
4. On Enter: `PlaybackManager.set_track("audio", track_id)` via IPC
5. Per-item audio choice persistence (like `subtitle_choices`)
6. `audio_choice_label()` for bottom status bar
7. Investigate Jellyfin default audio track selection

**New state**: `audio_choices: dict[str, str]` in `UIState`

**Files**: `jbrowse.py`, `tools/svg_screenshot_poc.py` (new capture)

---

### 3. Better Help Text / Key Map Cleanup
**Priority**: MEDIUM
**Effort**: Small (~50 lines reorganization)

**Current**: Flat list of all hotkeys
**Proposed sections**: Browsing, Search, Info, Playback, Themes, App

**Also**: `Ctrl+Shift+X` reverse theme cycling may not be reliably distinguishable from `Ctrl+X` in terminals. Consider alternatives.

---

### 4. README Screenshot Update
**Priority**: MEDIUM
**Effort**: Small

Choose best 10 screenshots from 31+ harness captures. Update `README.md`.

---

### 5. Server-Side Safety Guard
**Priority**: DONE (already implemented)

`post_server_mutation()` checks endpoint against `SERVER_MUTATION_OPERATIONS`. Future features must register here.

---

### 6. Bottom Bar Progress Bar (Deferred)
**Priority**: LOW (user said defer)
**Effort**: Small (if approved)

Add visual `█░` progress bar to bottom status bar during playback.

---

### 7. Jump to Time Feature (Other Agent)
**Priority**: DONE (other agent implemented)

Press `j` on Now Playing, type MM:SS or HH:MM:SS, Enter to jump via IPC `seek_to()`.

---

### 8. File Splitting (Architectural)
**Priority**: LOW (do after features stabilize)
**Effort**: Large

Split `jbrowse.py` (4025 lines) into modules. See `code-split-analysis.md` for detailed plan.

---

### 9. Test Harness Refactoring
**Priority**: MEDIUM (enables future testing)
**Effort**: Medium

Split `svg_screenshot_poc.py` (1060 lines) into modules. See `test-harness-analysis.md` for detailed plan.

---

### 10. Build Files / Arch Packaging
**Priority**: LOW (final step)
**Effort**: Medium

`pyproject.toml`, `PKGBUILD`, LICENSE, Makefile, install script, desktop file, man page, shell completion.

---

## Recommended Execution Order
1. Replace prompt wording (small, user-requested)
2. Audio picker (medium, natural next feature)
3. Help text cleanup (small)
4. README screenshot update (small)
5. Test harness refactoring (medium, enables future testing)
6. File splitting (large, architectural)
7. Build/packaging (final step)

## Verification Standards
Every feature must pass:
```bash
python -m py_compile jbrowse.py        # or jbrowse/ after split
python tools/svg_screenshot_poc.py --item otter
```

## Version Bump
- Update `CLIENT_VERSION` in `jbrowse.py`: `"0.0.34"` → `"0.0.35"`
- Update version in `README.md`
- Add `CHANGELOG.md` entry for 0.0.35
