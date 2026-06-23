# Code Split Analysis — jbrowse.py → Modules

## Current State
`jbrowse.py` is **4025 lines** in a single file. Contains: data models, Jellyfin API client, playback management, UI, themes, config, caching, and main app loop.

## Module Breakdown

### Proposed Structure
```
jbrowse/
├── __init__.py          # Package marker, public API re-exports
├── constants.py         # Imports, constants, SERVER_MUTATION_OPERATIONS
├── models.py            # Data classes (Theme, UIState, MediaItem, etc.)
├── config.py            # Config/State/Auth loading and persistence
├── themes.py            # Theme discovery and management
├── jellyfin.py          # Jellyfin API client (JellyfinClient, FakeJellyfinClient)
├── parsing.py           # Media item parsing and formatting
├── cache.py             # Item cache persistence
├── player.py            # Playback management and IPC (PlaybackManager)
├── ui.py                # All UI code (BrowseApp, ItemPane, browser_loop)
└── __main__.py          # Entry point (main function)
```

### Detailed Module Specifications

#### `constants.py` (~99 lines, lines 1-99)
**Content**: All module-level constants and imports
- `APP_NAME`, `CLIENT_VERSION`, `TICKS_PER_SECOND`
- `DEFAULT_VISIBLE_ITEMS`, `CACHE_VERSION`, `DEFAULT_MPV_CMD_TEMPLATE`
- `DEFAULT_REFRESH_INTERVAL_MINUTES`, `REFRESH_ACTIVE_WINDOW_SECONDS`
- `REFRESH_CHECK_SECONDS`, `SORT_MODE_ORDER`, `SORT_MODE_LABELS`
- `SERVER_MUTATION_OPERATIONS`
- Standard library imports

**Dependencies**: None (stdlib only)

---

#### `models.py` (~150 lines, lines 245-458)
**Content**: All data classes
- `Theme` (name, path, tcss)
- `ThemeCycle` (direction)
- `PlaybackRequest` (item, subtitle_choice)
- `PlaybackResult` (return_code, command, output)
- `UIState` (view, display_mode, sort_desc, query, selected_item_id, scroll_offset, focus, page, previous_page, info_item_id, info_scroll, mpv_log_scroll, now_playing_scroll, subtitle_choices, audio_choices, quality_index, quality_flash, quality_flash_until, previous_page)
- `SubtitleTrack` (key, title, mpv_sid, language, default, forced, external)
- `Config` (path, jellyfin_url, username, password, item_types, initial_view, sort_mode, sort_desc, display_mode, quality_presets, default_quality, style_path)
- `State` (path, deviceid)
- `Auth` (user_id, token)
- `MediaItem` (id, title, filename, kind, series_name, season_number, episode_number, premiere_date, date_created, last_played, resume_ticks, runtime_ticks, info_lines, subtitle_tracks)

**Dependencies**: constants

---

#### `config.py` (~200 lines, lines 100-244, 511-615)
**Content**: Configuration loading and persistence
- `script_dir()`, `die()`, `default_cfg_path()`, `default_state_path()`, `default_item_cache_path()`, `default_mpv_log_path()`, `default_style_path()`
- `expand_style_path()`, `style_path_for_config()`
- `persist_style_path()`, `persist_ui_values()`, `persist_display_mode()`, `persist_sort_state()`
- `load_cfg()`, `load_state()`, `load_mpv_cmd()`

**Dependencies**: constants, models

---

#### `themes.py` (~120 lines, lines 341-458)
**Content**: Theme discovery and management
- `read_tcss()`, `initial_theme()`, `discover_themes()`

**Dependencies**: constants, models, config

---

#### `jellyfin.py` (~325 lines, lines 459-783)
**Content**: Jellyfin API client
- `JellyfinError`, `missing_cfg_message()`
- `is_placeholder_token()`, `token_has_placeholder()`
- `JellyfinClient` (auth_header, headers, login, fetch_items, stream_url, post_server_mutation, report_playback_started/progress/stopped)
- `FakeJellyfinClient` (stream_url, fetch_items, report_playback_*)

**Dependencies**: constants, models, config

---

#### `parsing.py` (~490 lines, lines 784-1273)
**Content**: Media item parsing and formatting
- `optional_int()`, `parse_item()`, `make_title()`, `make_filename()`
- `format_seconds()`, `format_runtime_minutes()`, `format_progress()`, `format_date_short()`
- `first_media_path()`, `first_media_source()`, `media_streams()`, `stream_display_title()`
- `first_stream_title()`, `best_subtitle_title()`, `subtitle_track_title()`, `subtitle_tracks()`
- `add_kv()`, `add_section()`, `stream_lines()`, `technical_detail_lines()`
- `make_info_lines()`, `add_progress_info_line()`, `parse_jf_date()`
- `title_sort_key()`, `series_sort_key()`, `sorted_views()`, `find_item_by_id()`

**Dependencies**: constants, models

---

#### `cache.py` (~150 lines, lines 1274-1425)
**Content**: Item cache persistence
- `media_item_to_cache()`, `subtitle_track_from_cache()`, `media_item_from_cache()`
- `load_item_cache()`, `write_item_cache()`
- `fake_cache_data_path()`, `load_fake_cache_data()`, `load_fake_items()`

**Dependencies**: constants, models, parsing

---

#### `player.py` (~540 lines, lines 3339-3878)
**Content**: Playback management and IPC
- `subtitle_track_for_choice()`, `debug_mpv_command()`, `expand_mpv_token()`
- `build_mpv_command()`, `default_mpv_ipc_path()`
- `PlaybackManager` (__init__, write_log, position_ticks, playback_payload, report, is_active, stop_active, _progress_reporter_worker, _start/stop_progress_reporter, snapshot, append_output, _ipc_connect, _ipc_send, _ipc_recv_response, _ipc_get_number, ipc_get_property, ipc_set_property, ipc_command, toggle_pause, seek_to, seek_relative, loadfile_replace, set_track, stop_via_ipc, _ipc_close, start_background, read_output_worker, wait_for_background_playback, run)
- `play_item()` wrapper

**Dependencies**: constants, models, config, jellyfin

---

#### `ui.py` (~2520 lines, lines 1426-3945)
**Content**: All UI code
- `ItemPane` widget
- `BrowseApp` class (__init__, compose, query, listbox, status, bottom_status, on_mount, on_input_changed, on_mouse_down, on_mouse_scroll_down, render_items, render_info, render_help, render_mpv_log, render_subtitle_picker, render_replace_prompt, render_now_playing, render_jump_to_time, open_now_playing, open_info, open_subtitle_picker, open_audio_picker, open_mpv_log, open_playback_control, start_playback, play_info_item, play_selected, _show_web_url, _cycle_quality, _apply_quality, _build_stream_url, _current_quality_label, _format_title_for_bar, _web_url, bottom_status_text, update_bottom_status, update_subtitle_status, _start_info_poll, _poll_info, _start_bottom_bar_poll, _poll_bottom_bar, _poll_now_playing, _scroll_now_playing, _seek_back, _handle_replace_key, _show_replace_prompt, _handle_playback_control_key, _open_playback_control, _render_playback_control, _handle_jump_to_time_key, _show_jump_to_time, _render_jump_to_time, _handle_jump_to_time_key, _jump_to_time_action, _jump_to_time_cancel, navigate_info_episode, navigate_info_season, scroll_info, scroll_mpv_log, find_item_by_id, _do_start_playback, _start_bottom_bar_poll)
- `browser_loop()`

**Dependencies**: ALL other modules

---

#### `__main__.py` (~80 lines, lines 3946-4025)
**Content**: Entry point
- `parse_args()`, `main()`

**Dependencies**: All modules

---

## Dependency Graph
```
constants.py (no deps)
    ├── models.py
    │   ├── config.py
    │   │   ├── themes.py
    │   │   └── jellyfin.py
    │   │       └── player.py
    │   ├── parsing.py
    │   │   └── cache.py
    │   └── ui.py (depends on ALL)
    │       └── __main__.py
```

## Migration Strategy

### Phase 1: Extract Leaf Modules (no internal dependencies)
1. Create `jbrowse/` package directory with `__init__.py`
2. Extract `constants.py` — pure constants, no imports from jbrowse
3. Extract `models.py` — data classes, only imports constants
4. Extract `config.py` — uses constants + models
5. Verify: `python -m py_compile jbrowse/`

### Phase 2: Extract API and Parsing Layers
6. Extract `jellyfin.py` — uses constants + models + config
7. Extract `parsing.py` — uses constants + models
8. Extract `cache.py` — uses constants + models + parsing
9. Extract `themes.py` — uses constants + models + config
10. Verify: `python -m py_compile jbrowse/`

### Phase 3: Extract Player and UI
11. Extract `player.py` — uses constants + models + config + jellyfin
12. Extract `ui.py` — uses everything
13. Extract `__main__.py` — uses everything
14. Verify: `python -m py_compile jbrowse/`

### Phase 4: Update Harness and Verify
15. Update `tools/svg_screenshot_poc.py` imports to use `jbrowse.*`
16. Run full harness: `python tools/svg_screenshot_poc.py --item otter`
17. Run `--real` smoke test
18. Delete `jbrowse.py`

## Risk Assessment

**High risk areas:**
- `BrowseApp.__init__()` has ~40 lines of state initialization referencing many modules
- `browser_loop()` creates `BrowseApp` with many constructor arguments
- Cross-module references like `format_progress`, `TICKS_PER_SECOND`, `SERVER_MUTATION_OPERATIONS`

**Low risk areas:**
- `constants.py` and `models.py` are self-contained
- `cache.py` and `parsing.py` have clear interfaces
- `player.py` only needs JellyfinClient from jellyfin.py

## Additional Code Quality Items

### 1. Type Hints
- Add return types to all public methods
- Use `Optional[]` instead of `| None` for Python 3.9 compatibility
- Add type aliases for complex types (e.g., `type JsonDict = dict[str, Any]`)

### 2. Docstrings
- Add module-level docstrings to each new file
- Add docstrings to all public classes and methods
- Use Google-style or NumPy-style docstrings consistently

### 3. Constants Extraction
- Move magic numbers to named constants (e.g., `SETTLE_PAUSE_SECONDS = 0.3`)
- Group related constants into enums where appropriate (e.g., `Page`, `Overlay`)

### 4. Error Handling
- Create custom exception hierarchy (`JellyfinError`, `PlaybackError`, `UIError`)
- Add context to error messages (which item, which operation)

### 5. Logging
- Replace `print()` calls with proper `logging` module
- Use different log levels (DEBUG, INFO, WARNING, ERROR)
- Add structured logging for playback events

### 6. Configuration Validation
- Add validation for config values on load
- Provide sensible defaults for missing config
- Add config migration for old config formats
