# CHANGELOG.md

## 0.0.31 - 2026-06-19

Theme order and SVG screenshot harness release.

Changes:

- Renamed committed themes with numeric prefixes so `Ctrl+X` cycles in a deliberate order.
- Removed the white-background `jbrowse-ayu.tcss` theme.
- Removed the real-terminal PNG screenshot POC.
- Rebuilt the SVG screenshot harness around Textual `run_test` and normal pilot key presses.
- Added simple screenshot checks before writing SVG files for browser, theme cycle, info, subtitles, help, and refresh state.
- Updated docs and config examples for the numbered theme names.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/svg_screenshot_poc.py`.
- Passed `./jbrowse.py --print-style-path`.
- Ran `python tools/svg_screenshot_poc.py`.
- Confirmed screenshots are written directly under ignored `screenshot/`.
- Confirmed `after-ctrl-x.svg` is produced by pressing `Ctrl+X` and then using the next discovered theme.

Manual release check:

- Open the app and press `Ctrl+X`; confirm the next numbered theme appears and is saved.
- Review `screenshot/browser.svg`, `screenshot/info.svg`, `screenshot/subtitles.svg`, `screenshot/help.svg`, and `screenshot/refreshing.svg`.

## 0.0.30 - 2026-06-19

Minimal playback reporting release.

Changes:

- Added a small `PlaybackManager` around foreground `mpv` playback.
- Added Jellyfin playback start/progress/stopped reports using `/Sessions/Playing` endpoints.
- Kept `mpv` foreground behavior unchanged.
- Estimate playback position from wall-clock time plus Jellyfin resume position, with accurate resume reporting left for mpv IPC.
- Made playback reporting nonfatal so local playback still works if Jellyfin reporting fails.
- Trigger a background refresh after playback returns so local cache/sort state can pick up playback metadata changes.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/ui_screenshot_poc.py`.
- Passed config/state/style path smoke checks.
- Confirmed `PlaybackManager` sends start/progress/stopped reports with estimated position.
- Confirmed playback command construction still preserves subtitle and resume args.
- Confirmed returning from playback schedules a background refresh.
- Ran a real Jellyfin playback-reporting smoke test with a no-video command and confirmed `LastPlayedDate` updated.
- Ran a real 5-second `mpv` smoke test and confirmed Jellyfin `LastPlayedDate` updated and `PlayCount` incremented.
- Ran `python tools/ui_screenshot_poc.py` against the real configured Jellyfin server.
- Confirmed future mpv IPC / player config guard strings only appear in `AGENTS.md`.

Manual release check:

- Play an item and confirm Jellyfin recently played state updates.
- Confirm the app refreshes after playback returns so local last-played sorting updates.
- Confirm normal playback still works if Jellyfin playback reporting fails.
- Confirm subtitle choices still reach `mpv`.

## 0.0.29 - 2026-06-19

Periodic refresh release.

Changes:

- Added `[cache] refresh_interval_minutes`, defaulting to `10`.
- Periodic refresh reuses the existing background refresh path.
- Periodic refresh only runs if `jbrowse` has been active in the last 10 minutes.
- Foreground playback counts as inactive, so periodic refresh waits until the app is active again.
- Documented the cache refresh config in README and `jbrowse.conf.example`.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/ui_screenshot_poc.py`.
- Passed config/state/style path smoke checks.
- Confirmed periodic refresh starts when due and recently active.
- Confirmed periodic refresh does not start while inactive.
- Confirmed activity after an inactive due interval starts periodic refresh.
- Confirmed returning after simulated playback can trigger due periodic refresh.
- Ran `python tools/ui_screenshot_poc.py` against the real configured Jellyfin server.
- Confirmed future mpv IPC / Jellyfin playback-reporting guard strings only appear in `AGENTS.md`.

Manual release check:

- Set `refresh_interval_minutes = 1`, use the app, and confirm refresh appears in the bottom bar after the interval.
- Leave the app idle past the active window and confirm refresh waits until activity resumes.
- Confirm manual `Ctrl+R` and normal playback still work.

## 0.0.28 - 2026-06-19

Non-blocking refresh release.

Changes:

- Open from the item cache first, then automatically refresh Jellyfin in the background.
- Made `Ctrl+R` refresh Jellyfin in the background instead of blocking the UI.
- Allowed `Ctrl+R` from info, subtitle, help, and browser screens.
- Show refresh state in the bottom status bar.
- Preserve the current search/list/info state when refreshed items arrive.
- Added a screenshot POC view using a fake refresh state for the refresh bottom-bar UI.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/ui_screenshot_poc.py`.
- Passed config/state/style path smoke checks.
- Ran `python tools/ui_screenshot_poc.py` against the real configured Jellyfin server.
- Confirmed cached startup opens first and startup refresh shows in the bottom status bar.
- Confirmed `Ctrl+R` works from the info screen without blocking.
- Confirmed refreshed items are cached and the current info screen is preserved when possible.
- Confirmed `screenshot/refreshing.svg` uses a fake refresh state and shows `refreshing...` in the bottom bar.
- Confirmed future mpv IPC / Jellyfin playback-reporting guard strings only appear in `AGENTS.md`.

Manual release check:

- Start with an existing item cache and confirm the UI appears before refresh completes.
- Press `Ctrl+R` on the browser and confirm the bottom bar shows refresh state.
- Open an info screen, press `Ctrl+R`, and confirm the info screen stays usable.
- Confirm normal playback still works after a background refresh.

## 0.0.27 - 2026-06-18

Configurable mpv command release.

Changes:

- Added optional `[mpv] mpv_cmd` config as a single playback command template.
- Added placeholders for `$url`, `$filename`, `$title`, `$subtitle`, and `$start`.
- Kept subtitle and resume behavior in the command template instead of adding format-specific command selection.
- Documented the current no-server-write expectation and the future mutation boundary.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/ui_screenshot_poc.py`.
- Passed config/state/style path smoke checks.
- Confirmed default `mpv_cmd` expands to the previous playback command shape.
- Confirmed custom `mpv_cmd` parsing and placeholder expansion.
- Confirmed subtitle placeholders expand for `auto`, `none`, and selected subtitle tracks.
- Ran `python tools/ui_screenshot_poc.py` against the real configured Jellyfin server.
- Confirmed future mpv IPC / Jellyfin playback-reporting guard strings only appear in `AGENTS.md`.

Manual release check:

- Play one item with `auto`, `none`, and a selected subtitle track.
- Confirm the `DEBUG mpv command` line shows the expected expanded command.
- Confirm normal playback and screenshots still work.

## 0.0.26 - 2026-06-18

Real-server UI screenshot POC.

Changes:

- Added `tools/ui_screenshot_poc.py` to harvest Textual SVG screenshots using the normal `jbrowse.conf`.
- Ignored local `screenshot/` output because it can contain private media names.
- Added a `BrowseApp` constructor switch so the screenshot harness can avoid rewriting the item cache during app construction.
- Cycle discovered themes in memory so each screenshot uses a different theme without saving to config.
- Added the active theme name to each SVG title because Textual's SVG renderer can make different dark themes look very similar.

Testing summary:

- Passed `python -m py_compile jbrowse.py tools/ui_screenshot_poc.py`.
- Ran `python tools/ui_screenshot_poc.py` against the real configured Jellyfin server.
- Confirmed `browser.svg`, `info.svg`, `subtitles.svg`, and `help.svg` were created under ignored `screenshot/`.
- Confirmed screenshots used different themes without modifying `jbrowse.conf`.
- Theme names are reflected in the SVG titles, but the visual differences are limited in the current SVG output and need another look later.

Manual release check:

- Run `python tools/ui_screenshot_poc.py`.
- Confirm `screenshot/browser.svg`, `screenshot/info.svg`, `screenshot/subtitles.svg`, and `screenshot/help.svg` are created.
- Confirm the screenshots use different themes and the configured theme in `jbrowse.conf` did not change.

## 0.0.25 - 2026-06-18

Subtitle picker release.

Changes:

- Added subtitle metadata to cached media items.
- Added an info-page subtitle picker opened with `s`.
- Added runtime per-item subtitle choices: `auto`, `none`, or a selected Jellyfin subtitle stream.
- Passed subtitle choices to `mpv` best-effort with `--sid=no` or `--sid=N`.
- Added a redacted `DEBUG mpv command` print to help inspect subtitle launch arguments.
- Stopped unhandled info/subtitle picker keys from leaking into the search box.
- Disabled search input while info/help/subtitle overlays are open so hotkeys do not leak into search after returning from `mpv`.
- Show the current subtitle choice in the bottom status bar on info/subtitle screens.
- Bumped item cache version to refresh subtitle metadata.
- Updated README, AGENTS notes, `CHANGELOG.md`, and `todo.md`.

Testing summary:

- Passed `python -m py_compile jbrowse.py`.
- Passed config/state/style path smoke checks.
- Confirmed future mpv IPC / Jellyfin playback-reporting guard strings only appear in `AGENTS.md`.
- Manual subtitle selection testing passed.
- No regressions were noticed in normal browsing/playback.

Manual release check used:

- Try `auto`, `none`, and a real subtitle track from the info panel.
- Confirm the selected subtitle is visible in the bottom status bar.
- On the info panel, press an unused letter key and confirm it does not appear in search.
- After `mpv` closes back to the info panel, press `s` and confirm the subtitle picker opens.

## 0.0.24

Baseline before this changelog.

Highlights:

- Fast single-`Static` media list renderer.
- Sort modes and persisted sort state.
- Regex search.
- Info page with media details and episode navigation.
- Foreground `mpv` playback with Jellyfin resume start position.
- Theme cycling and named theme files.
- Simple item cache.

Testing summary:

- Historical baseline; future releases should include the exact smoke/manual checks used.
