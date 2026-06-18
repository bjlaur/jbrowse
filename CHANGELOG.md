# CHANGELOG.md

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
