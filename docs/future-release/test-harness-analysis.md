# Test Harness Refactoring Analysis

## Current State
`tools/svg_screenshot_poc.py` is **1060 lines**. Started as a "proof of concept" and grew into the full test harness. It mixes test infrastructure, fake data, real-mpv tests, SVG verification, and 31+ view captures all in one file.

## Problems

1. **Single file** — 1060 lines with mixed concerns
2. **No shared fixtures** — Each view handler creates its own app instance
3. **Growing capture list** — 31+ views with inline key-press sequences
4. **Real-mpv tests are fragile** — IPC connection timing, stale sockets
5. **Hard to add new captures** — Must understand the entire file structure
6. **No test isolation** — Shared mutable state between captures
7. **View handlers are inline** — `elif view == "..."` chain is 400+ lines

## Proposed Module Structure

```
tools/
├── conftest.py          # Shared fixtures: settle(), quick_settle(), export_view(), make_state(), choose_demo_item()
├── fixtures.py          # Fixture data: FixtureClient, _FakeProcess, _FakeIpcSock, _setup_fake_playback, _make_long_filename_item()
├── svg_check.py         # SVG verification: check_svg(), check_theme_svg()
├── real_mpv_tests.py    # Real-mpv tests: run_real_mpv_smoke(), run_real_mpv_bitrate_test(), run_real_mpv_jump_test()
├── views.py             # All view handlers (grouped by category)
└── main.py              # CLI args, main(), view dispatch table
```

## Detailed Module Specifications

### `svg_check.py` (~30 lines)
**Purpose**: Pure SVG verification functions
**Content**:
- `check_svg(name, svg, expected)` — verifies expected text in SVG output
- `check_theme_svg(name, svg, theme)` — verifies theme background color in SVG

**Dependencies**: None (stdlib only: `html`, `re`)

---

### `fixtures.py` (~150 lines)
**Purpose**: All fake/test data
**Content**:
- `_FakeState` — fake device ID for FixtureClient
- `FixtureClient` — fake Jellyfin client (stream_url, fetch_items, report_playback_*)
- `_FakeProcess` — fake subprocess.Popen (poll, terminate, kill)
- `_FakeIpcSock` — fake IPC socket (sendall, recv, close, settimeout)
- `_setup_fake_playback(app, item)` — sets up fake active playback on app
- `_make_long_filename_item()` — creates item with very long filename
- `_FAKE_IPC_VALUES` — dict of fake IPC property values
- `_fake_paused` — mutable state for fake pause toggle
- `fixture_cfg()` — creates fixture Config
- `fixture_items()` — loads fake items from compressed fixture data
- `real_demo_data()` — loads real Jellyfin config/cache/items
- `fake_playback_item()` — creates a fake playback item
- `run_playback_smoke()` — fake playback smoke test

**Dependencies**: `jbrowse` (Config, MediaItem, PlaybackManager, etc.)

---

### `conftest.py` (~100 lines)
**Purpose**: Shared test infrastructure
**Content**:
- `settle(app, pilot)` — full settle with style cache clear + 0.3s pause
- `quick_settle(app, pilot)` — lightweight settle for post-key-press (0.2s pause)
- `make_state(cfg, item)` — creates UIState from config + item
- `choose_demo_item(items, query)` — picks demo item from list
- `export_view(cfg, client, items, demo_item, theme, size, output_path, view, expected)` — creates BrowseApp, runs pilot, dispatches to view handler, captures SVG

**Dependencies**: `jbrowse`, `fixtures`

---

### `views.py` (~450 lines)
**Purpose**: All view handler functions, grouped by category

**Content** — Each function has signature: `(app, pilot, demo_item) -> None`

**Browser views**:
- `view_browser(app, pilot)` — default browser view
- `view_after_ctrl_x(app, pilot)` — browser after theme cycle
- `view_search(app, pilot)` — search with "otter" query

**Info views**:
- `view_info(app, pilot)` — info page
- `view_info_playing(app, pilot)` — info page for playing item (live IPC progress)
- `view_info_backspace_to_browser(app, pilot)` — info page backspace

**Overlay views**:
- `view_subtitles(app, pilot)` — subtitle picker
- `view_help(app, pilot)` — help overlay
- `view_mpv_log(app, pilot)` — mpv log page
- `view_refreshing(app, pilot)` — refreshing state
- `view_web_url(app, pilot)` — web URL overlay from info page
- `view_web_url_info_overlay(app, pilot)` — web URL from info page
- `view_web_url_now_playing_overlay(app, pilot)` — web URL from Now Playing

**Playback views**:
- `view_now_playing(app, pilot)` — Now Playing page
- `view_ctrl_n_now_playing(app, pilot)` — Now Playing via Ctrl+N
- `view_space_pause(app, pilot)` — pause via Space
- `view_seek_comma_period(app, pilot)` — seek via comma/period
- `view_ctrl_k_stop(app, pilot)` — stop via Ctrl+K
- `view_now_playing_backspace_to_info(app, pilot)` — backspace from NP to info

**Replace prompt views**:
- `view_replace_prompt(app, pilot)` — replace confirmation overlay
- `view_replace_n_to_info(app, pilot)` — cancel replace → returns to info

**Playback control views**:
- `view_playback_control(app, pilot)` — Ctrl+P overlay
- `view_ctrl_p_from_browser(app, pilot)` — Ctrl+P from browser
- `view_now_playing_quality(app, pilot)` — quality cycle flash
- `view_ctrl_b_bitrate(app, pilot)` — bitrate cycle (quality label check)

**Jump to time views**:
- `view_jump_to_time(app, pilot)` — jump-to-time overlay

**Bottom bar views**:
- `view_bottom_bar_format(app, pilot)` — bottom bar format check
- `view_bottom_bar_long_name(app, pilot)` — long filename truncation

**Dependencies**: `jbrowse`, `fixtures`, `conftest`

---

### `real_mpv_tests.py` (~250 lines)
**Purpose**: All real-mpv integration tests
**Content**:
- `run_real_mpv_smoke(cfg, client, item, play_duration)` — basic IPC smoke test
- `run_real_mpv_bitrate_test(cfg, client, item, play_duration)` — bitrate cycling test
- `run_real_mpv_jump_test(cfg, client, item, play_duration)` — jump-to-time test
- `_build_stream_url_for_test(client, item, quality)` — builds Jellyfin transcoding URL
- `_cleanup_stale_sockets()` — removes stale IPC sockets before tests

**Dependencies**: `jbrowse`, `fixtures`, `conftest`

---

### `main.py` (~120 lines)
**Purpose**: CLI entry point and view dispatch
**Content**:
- `parse_args()` — CLI argument parsing (all --real, --view, --item, etc.)
- `main()` — orchestrates everything:
  1. Parse args
  2. Load config/data (fixture or real)
  3. Handle --real-mpv, --real-mpv-bitrate, --real-mpv-jump flags
  4. Handle --ipc-only flag
  5. Handle --view single capture
  6. Run full harness (all captures)
  7. Handle --all-themes
- `VIEW_DISPATCH` — dict mapping view name → handler function

**Dependencies**: All modules

---

## Migration Strategy

### Phase 1: Extract pure utilities
1. Extract `svg_check.py` — no dependencies
2. Verify: `python -m py_compile tools/svg_check.py`

### Phase 2: Extract fixtures
3. Extract `fixtures.py` — fake data and clients
4. Update `svg_screenshot_poc.py` to import from `fixtures`
5. Verify: full harness still passes

### Phase 3: Extract test infrastructure
6. Extract `conftest.py` — shared test functions
7. Update `svg_screenshot_poc.py` to import from `conftest`
8. Verify: full harness still passes

### Phase 4: Extract view handlers
9. Extract `views.py` — all view handler functions
10. Update `svg_screenshot_poc.py` to import from `views`
11. Verify: full harness still passes

### Phase 5: Extract real-mpv tests
12. Extract `real_mpv_tests.py` — real-mpv test functions
13. Update `svg_screenshot_poc.py` to import from `real_mpv_tests`
14. Verify: full harness still passes

### Phase 6: Split main
15. Extract `main.py` — CLI and orchestration
16. Create new entry point that imports from all modules
17. Delete `svg_screenshot_poc.py`
18. Verify: `python tools/main.py --item otter` runs all 31+ captures

## Risk Assessment

**High risk areas**:
- `export_view()` creates BrowseApp with many parameters — must be preserved exactly
- View handlers reference many jbrowse classes — need correct imports
- Real-mpv tests need careful async context handling

**Low risk areas**:
- `svg_check.py` is pure functions
- `fixtures.py` is self-contained
- View handlers are mostly independent

## Additional Code Quality Items for Harness

### 1. View Handler Registration
Use a decorator or registry pattern instead of if/elif chain:
```python
@register_view("now-playing")
def view_now_playing(app, pilot, demo_item):
    _setup_fake_playback(app, demo_item)
    app.open_now_playing()
    await settle(app, pilot)
```

### 2. Parameterized Captures
For views that differ only by key press, use parameters:
```python
@capture_view("space-pause", keys=["space"])
@capture_view("seek-comma", keys=[","])
@capture_view("seek-period", keys=["."])
```

### 3. Shared App Setup
Create a base app fixture that all views can reuse:
```python
async def base_app(cfg, client, items, demo_item, theme):
    app = BrowseApp(cfg, client, items, theme.name, make_state(cfg, demo_item), ...)
    return app
```

### 4. Capture Metadata
Add metadata to each capture for documentation:
```python
CAPTURE_INFO = {
    "now-playing": {
        "description": "Now Playing page with live progress bar",
        "keys": ["ctrl+n"],
        "category": "playback",
    },
    ...
}
```

### 5. Screenshot Selection Helper
Add a function to select best screenshots based on criteria (see `screenshot-analysis.md`)
