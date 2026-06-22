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
- **Every commit MUST update `AGENTS.md`, `TODO.md`, and `CHANGELOG.md`** to reflect the current state. No code commit without corresponding docs updates.

## Release Checklist

Before every release, run through this entire list. Do not skip steps.

### Code & Compilation
- [ ] `python -m py_compile jbrowse.py` — no syntax errors
- [ ] `python -m py_compile tools/svg_screenshot_poc.py` — no syntax errors

### Automated Screenshot Harness
- [ ] `python tools/svg_screenshot_poc.py --item otter` — all 8 SVGs pass checks
- [ ] If UI changed: verify new screenshots look correct in `tools/screenshot/`
- [ ] If new UI page or overlay: add a capture step to the harness

### IPC / Playback Smoke Tests (requires `--real` + Jellyfin cache)
- [ ] `python tools/svg_screenshot_poc.py --ipc-only --real --play-duration 5`
- [ ] Verify IPC time-pos ≈ elapsed time (within tolerance)
- [ ] Verify Jellyfin start/progress/stopped reports accepted in local playback log
- [ ] Test pause toggle (Space), seek (,/.), stop (Ctrl+K) manually
- [ ] Test replace playback prompt (play item, navigate to another, press Enter)
- [ ] Test Now Playing page (Ctrl+N) — progress bar, track info
- [ ] Test playback control menu (Ctrl+P) — all controls work
- [ ] Test quality cycle (Ctrl+B) — status message shown

### Full Theme Gallery (major releases only)
- [ ] `python tools/svg_screenshot_poc.py --item otter --all-themes`
- [ ] Verify all themes render without errors in `docs/themes/`
- [ ] Spot-check 3–4 theme SVGs visually for correct colors

### Documentation Updates (every commit AND release)
- [ ] `AGENTS.md` — update "Current Playback / IPC Status" section, mark phases complete
- [ ] `TODO.md` — check off completed items, update "Next" pointer
- [ ] `CHANGELOG.md` — add release entry with changes + testing summary + manual release check steps
- [ ] `README.md` — update version number, features list, controls reference, config example
- [ ] `jbrowse.conf.example` — add any new config sections

### Final Verification
- [ ] Review all changed files: `git diff --stat`
- [ ] Commit message is short (~8 words), imperative mood
- [ ] Ask user before committing: "I just made my last changes before commit/push. Good to continue?"
- [ ] Ask user before pushing to remote

## Near-Term Roadmap

1. Stabilize the promoted 0.0.34 baseline.
2. Server-side safety guard.
3. Audio picker.
4. Better help text / key map cleanup.
5. Split into modules (later, after architecture stabilizes).
6. Build/packaging/Arch PKGBUILD.

Keep those phases separate. Do not bundle threaded refresh, mpv IPC, and playback reporting into one large change.

## Current Playback / IPC Status

- mpv IPC is active: `PlaybackManager` connects to mpv via `--input-ipc-server` Unix socket.
- IPC provides: `ipc_get_property`, `ipc_set_property`, `ipc_command`, `toggle_pause`, `seek_to`, `seek_relative`, `loadfile_replace`, `set_track`, `stop_via_ipc`.
- `stop_active()` tries IPC `stop` first, falls back to `terminate()`.
- `position_ticks()` uses IPC `time-pos` first, falls back to wall-clock estimation.
- Periodic progress reporter sends Jellyfin `/Sessions/Playing/Progress` every 5s via IPC.
- `playback_payload()` reads `pause` state from IPC.
- Bottom status bar shows live playback state: `playing/paused: <title> <position>`.
- Each playback writes a private log to `~/.cache/jbrowse/mpv.out-YYYYMMDD-HHMMSS-ffffff`.
- Completed: All IPC feature phases (1–6) + playback control menu.
- Phase 1: Low-level IPC socket layer
- Phase 2: Accurate Jellyfin reporting via IPC time-pos
- Phase 3: Replace-current-playback prompt with loadfile_replace
- Phase 4: Pause/stop/seek controls (Space, comma, period)
- Phase 5: Now Playing page (Ctrl+N) with live progress bar
- Phase 6: Static bitrate selection (Ctrl+B) with quality cycling
- Playback control menu: Ctrl+P for global playback overlay
- Manual release check for 0.0.34: see CHANGELOG.md section "Manual release check" under 0.0.34.
- Next: Server-side safety guard, audio picker, help text cleanup.
