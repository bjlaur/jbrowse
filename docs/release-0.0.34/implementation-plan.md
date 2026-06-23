# Plan: IPC Feature Implementation (Phases 2–6)

## Context

Phase 1 (low-level IPC socket layer) is complete and committed. `PlaybackManager` now connects to mpv via `--input-ipc-server`, and all IPC helpers (`ipc_get_property`, `toggle_pause`, `seek_to`, `loadfile_replace`, `stop_via_ipc`, etc.) are wired in and verified with `--real-mpv --play-duration`.

This plan covers the remaining 5 phases, all building on top of Phase 1.

**Current state**: `position_ticks()` still uses wall-clock estimation. Jellyfin reporting uses estimated position. The UI has no Now Playing page, no replace-playback prompt, no pause/seek controls.

## Remaining Phases

### Phase 2: Accurate Position & Jellyfin Reporting

**Goal**: Use IPC `time-pos` for accurate playback position and send proper Jellyfin progress reports.

1. Update `position_ticks()`:
   - Try `self._ipc_get_number("time-pos")` first
   - Fall back to existing wall-clock estimation if IPC unavailable
   - Return `int(time_pos * TICKS_PER_SECOND)` on success

2. Add periodic progress reporter:
   - In `start_background()`, spawn a daemon thread that:
     - Every 5 seconds, checks `is_active()`
     - Reads `time-pos` via IPC
     - Sends Jellyfin `/Sessions/Playing/Progress` with accurate position
     - Reads `pause` state via IPC, includes in payload
   - Thread exits when playback ends or `ipc_socket_path` is None

3. Update `wait_for_background_playback()`:
   - Signal the progress reporter thread to stop
   - Join the reporter thread with timeout
   - Use IPC `time-pos` for final position in stopped report

4. Update `playback_payload()`:
   - Read `pause` state from IPC instead of hardcoding `False`

**Verification**: `--ipc-only --real --play-duration 10` — check that reported position ≈ elapsed time.

---

### Phase 3: Replace-Current-Playback Prompt

**Goal**: When something is already playing, ask before starting a new playback.

1. In `BrowseApp.start_playback()`:
   - If `playback_manager.is_active()`, store the pending item and show confirm overlay
   - Otherwise start normally (existing behavior)

2. Add `pending_playback_item` state to `BrowseApp`

3. Add confirmation overlay method:
   - Shows "Currently playing: X" / "Replace with: Y?" / "y replace | n cancel"
   - Rendered as an overlay panel (like subtitles/help)
   - `y` → call `playback_manager.loadfile_replace(new_url)` via IPC, start new Jellyfin session
   - `n` → cancel, return to browser
   - `q`/`Escape`/`backspace` → cancel

4. Jellyfin session transition on replace:
   - Stop old session (send "stopped" report via IPC position)
   - Generate new `play_session_id`
   - Send "started" report for new item

5. `UIState`: add `pending_playback_item_id: str`

**Verification**: Run harness, start playback, try to start another → confirm overlay appears.

---

### Phase 4: Pause/Stop/Seek Controls

**Goal**: Control playback from within the browser UI.

1. `Space` — toggle pause/play:
   - Works from browser page when playback is active
   - Calls `playback_manager.toggle_pause()`
   - Show brief status message ("playing" / "paused") in bottom bar

2. `,` / `.` — seek -10s / +10s:
   - Works from browser page when playback is active
   - Calls `playback_manager.seek_to(current_pos ± 10)`
   - Show brief status message ("seeked to MM:SS") in bottom bar

3. `Ctrl+K` — already exists for stop

4. Brief status messages:
   - Use a `set_timer` auto-clearing message in bottom bar (3s timeout)
   - Don't interfere with existing refresh/error messages

5. Update help page:
   - Add "Space pause/play", ",/. seek ±10s" to Playback section

**Verification**: Play something via `--real-mpv`, test pause/seek/resume.

---

### Phase 5: Now Playing Page

**Goal**: Live playback state page with progress bar and track info.

1. Add `"now_playing"` to `BrowseApp` page set alongside browser/help/info/subtitles/mpv_log

2. Hotkey: `Ctrl+N` in browser

3. Render layout:
   ```
   Now Playing 8/10
   q/backspace browser | Space pause | ,/. seek | s subtitles | Ctrl+G mpv log

   Season 4 - 8. Episode Title
   ████████████░░░░░░░░░░░░░░  12:43 / 58:00
   state: playing    quality: direct    subtitle: English - SUBRIP

   Video       4K HEVC SDR
   Audio       English - Dolby Digital+ - 5.1 - Default
   Subtitles   English - SUBRIP

   Synopsis...
   ```

4. Poll IPC every 1s via `set_timer`:
   - `time-pos` → update progress bar and position text
   - `duration` → update total time
   - `pause` → update state display
   - `track-list` → update video/audio/subtitle info (on first load + on change)
   - Stream stats from `PlaybackManager.snapshot()` also available

5. Progress bar: use Textual `rich.text.Text` with block characters (█░) proportional to position/duration

6. Episode navigation: ←/→ jump to next/prev episode (if same series), loadfile_replace

7. Add `now_playing_scroll: int` to `UIState`

8. Handle "playback ended" transition: auto-return to browser when mpv exits while on Now Playing page

**Verification**: `--real-mpv` → Ctrl+N → verify progress bar moves, pause from page works.

---

### Phase 6: Static Bitrate Selection (Deferred)

**Goal**: Cycle through quality presets without stopping playback.

1. Add `[playback]` section to config:
   ```ini
   [playback]
   quality_presets = direct,40mbps,20mbps,12mbps,8mbps,4mbps,2mbps
   default_quality = direct
   ```

2. Hotkey: `Ctrl+B` to cycle forward through presets

3. Quality display in bottom bar: `quality: direct`

4. On quality change:
   - Get current `time-pos` via IPC
   - Build new Jellyfin URL:
     - `direct` = current static stream URL (no change)
     - Others = add `&MaxStreamingBitrate=<bits>` to transcoding URL
   - `loadfile_replace(new_url)` via IPC
   - Maintains same playback position

5. Jellyfin transcoding URL format:
   - `/Videos/{id}/stream?static=false&codec=h264&api_key=...&MaxStreamingBitrate=...`

**Verification**: `--real-mpv` → Ctrl+B → observe URL change in mpv output page.

---

## Key Files

- **`jbrowse.py`** — All changes (single-file app)
- **`jbrowse.conf.example`** — Add `[playback]` section (Phase 6)
- **`todo.md`** — Check off completed items per phase
- **`CHANGELOG.md`** — Entry per phase
- **`AGENTS.md`** — Update status as phases complete

## Verification Standards

Every phase must pass:
```bash
python -m py_compile jbrowse.py
python tools/svg_screenshot_poc.py --item otter
```

Phases using real playback additionally:
```bash
python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5
```

Then `git commit` with short message per phase.

---

## Execution Order

| Phase | Description | Dependencies | Effort |
|-------|-------------|-------------|--------|
| 2 | Accurate Jellyfin reporting | Phase 1 | Medium |
| 3 | Replace-playback prompt | Phase 1 | Medium |
| 4 | Pause/stop/seek controls | Phase 1 | Small |
| 5 | Now Playing page | Phase 2 (accurate position), Phase 3 (replace) | Large |
| 6 | Bitrate selection | Phase 3 (replace), Phase 4 | Medium |

Recommended: 2 → 4 → 3 → 5 → 6 (do controls early since they're small wins).

## Constraints

- IPC failures must be graceful — fall back to existing behavior, never crash
- `PlaybackManager` owns all IPC state; `BrowseApp` calls public methods only
- No new Python packages needed (all stdlib)
- Don't run `--all-themes` unless explicitly asked
- Keep `jbrowse.py` as single file
- Separate concerns: reporting, UI, controls in distinct changes
