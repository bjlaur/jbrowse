# CHANGELOG.md

## Unreleased

Experimental subtitle picker checkpoint. Not a release yet.

Changes:

- Added subtitle metadata to cached media items.
- Added an info-page subtitle picker opened with `s`.
- Added runtime per-item subtitle choices: `auto`, `none`, or a selected Jellyfin subtitle stream.
- Passed subtitle choices to `mpv` best-effort with `--sid=no` or `--sid=N`.
- Added a temporary redacted `DEBUG mpv command` print to help inspect subtitle launch arguments.
- Bumped item cache version to refresh subtitle metadata.
- Updated README, AGENTS notes, `CHANGELOG.md`, and `todo.md`.

Testing summary:

- Passed `python -m py_compile jbrowse.py`.
- Passed config/state/style path smoke checks.
- Confirmed future mpv IPC / Jellyfin playback-reporting guard strings only appear in `AGENTS.md`.
- Manual testing found that selected subtitles do not yet work correctly in `mpv`.

Manual release check:

- Fix subtitle selection, then try `auto`, `none`, and a real subtitle track from the info panel.

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
