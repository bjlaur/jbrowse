# jbrowse Agent Notes

## Project Shape

- `jbrowse` is a single-file Python/Textual Jellyfin browser and `mpv` launcher.
- The active script is `jbrowse.py`.
- Keep the app simple and practical. Do not split it into modules unless the user asks or the single file becomes a real blocker.
- Use Git history for rollback. Do not create new `jbrowse_fresh_0_XX.py` handoff files.

## User And Environment

- Assume Linux, specifically Arch/CachyOS with GNOME/Wayland.
- Prefer practical changes and concise explanations.
- Use `vim` in terminal examples when an editor example is needed.
- Prefer Arch-style package commands when mentioning system packages.
- Do not commit real local config, state, cache, or media-library data.
- **Do not `pip install` dependencies into the system Python.** The user is handling Python dependencies (textual, requests, rich, etc.) inside their Containerfile / environment, not via pip from the agent. If a dependency is missing, tell the user to add it to the Containerfile rather than installing it yourself.
- **Keep commit messages short — around 8 words.** Imperative mood, no body unless something truly needs explanation.
- **Always ask before committing.** Do not commit unless the user explicitly asks for it.
- **Let the user know if a new Python package is needed.** The user manages dependencies via the Containerfile — do not `pip install` anything yourself.

## Runtime Files

- Real config: `jbrowse.conf`; ignored because it contains Jellyfin credentials.
- Example config: `jbrowse.conf.example`; this is safe to commit.
- State file: `jbrowse.state`; ignored.
- Item cache: `jbrowse.items.json`; ignored because it can contain private media names/paths.
- Playback diagnostics: timestamped `~/.cache/jbrowse/mpv.out-*`; local because they can contain private media names and report details.
- Local style override: `jbrowse.tcss`; ignored. Named theme files belong under `themes/` and are safe to commit.

## Important Design Decisions

- Do not reintroduce Textual `ListView`/`ListItem` for media rows. The app uses one `Static` widget (`ItemPane`) that renders visible rows only; this is critical for large libraries.
- `Ctrl+I` is not suitable for info because terminals treat it as Tab.
- F2 was rejected as an info key. Current behavior is `Enter` for info and `Shift+Enter` for direct playback.
- No `[player]` config yet. `mpv` playback is intentionally simple, with only the lightweight `[mpv] mpv_cmd` command template.
- Manual and periodic refresh are backgrounded. Keep future refresh work separate from playback architecture.
- Named themes intentionally ignore inherited `NO_COLOR`; otherwise Textual flattens every theme to monochrome. `Ctrl+X` returns `ThemeCycle` and the outer browser loop rebuilds the app with the next theme; do not replace that flow with direct stylesheet swapping.
- Jellyfin playback reports are the only intentional server mutations. Register any future server write in `SERVER_MUTATION_OPERATIONS` before sending it; do not turn normal browse/cache/screenshot paths into server writes.

## Verification

After code changes, run:

```bash
python -m py_compile jbrowse.py
```

Useful lightweight checks:

```bash
./jbrowse.py --print-config-path
./jbrowse.py --print-state-path
./jbrowse.py --print-style-path
```

~~Avoid accidentally adding these before their planned feature work~~ — mpv IPC is now active:

```text
input-ipc-server   # used by PlaybackManager for IPC
[player]           # still deferred; no player config section yet
```

## Screenshots

- When a change adds or modifies a visible UI element, add or update a screenshot capture in `tools/svg_screenshot_poc.py` so the theme gallery reflects the new state.
- Do not regenerate the full theme gallery on every commit — only when the UI actually changes.
- The `--real-mpv` smoke test is a regression test only for IPC. It is not part of the normal smoke suite and requires `--real` plus a logged-in Jellyfin cache.
- Use `--ipc-only` to run *just* the IPC smoke test without generating any screenshots. Fast path for playback/IPC work.
- `--all-themes` is on-demand only — run it when the theme gallery actually needs updating (release time, new themes, UI changes). Never run it as a routine check.

## Release Notes And Roadmap Hygiene

- Keep completed roadmap items in `todo.md` marked as done/crossed out instead of deleting them.
- After each release, add a small `CHANGELOG.md` entry.
- Each changelog entry should include a very small testing summary and note any important manual test gap.
- When the user says to commit and/or push, treat that request as a Git-only operation. Do not make further file changes in that step. If a file change is still needed, stop and ask: "I just made my last changes before commit/push. Good to continue?"

## Near-Term Roadmap

1. Stabilize the promoted 0.0.33 baseline.
2. Keep server-safety and background-playback follow-ups separate from mpv IPC.
3. Keep build/packaging polish lower priority unless explicitly requested.

Keep those phases separate. Do not bundle threaded refresh, mpv IPC, and playback reporting into one large change.

## Current Playback / IPC Status

- mpv IPC is active: `PlaybackManager` connects to mpv via `--input-ipc-server` Unix socket.
- IPC provides: `ipc_get_property`, `ipc_set_property`, `ipc_command`, `toggle_pause`, `seek_to`, `loadfile_replace`, `set_track`, `stop_via_ipc`.
- `stop_active()` tries IPC `stop` first, falls back to `terminate()`.
- `position_ticks()` still uses wall-clock estimation — Phase 2 will switch to IPC `time-pos`.
- Jellyfin playback reporting still uses estimated position — Phase 2 will add periodic IPC progress polls.
- Each playback writes a private log to `~/.cache/jbrowse/mpv.out-YYYYMMDD-HHMMSS-ffffff`.
- Next: Phase 2 — accurate Jellyfin reporting via IPC `time-pos`.
