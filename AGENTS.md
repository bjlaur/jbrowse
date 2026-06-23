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
- **Do not use any F keys (F1–F12).** Textual intercepts them for its own purposes (e.g., F1 opens the Textual command palette). Use `?` for help instead.
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
- **Every new UI page/overlay/prompt MUST have a corresponding capture in the harness.** Add a new entry to the `captures` list with expected text checks.
- Do not regenerate the full theme gallery on every commit — only when the UI actually changes.
- The `--real-mpv` smoke test is a regression test only for IPC. It is not part of the normal smoke suite and requires `--real` plus a logged-in Jellyfin cache.
- Use `--ipc-only` to run *just* the IPC smoke test without generating any screenshots. Fast path for playback/IPC work.
- `--all-themes` is on-demand only — run it when the theme gallery actually needs updating (release time, new themes, UI changes). Never run it as a routine check.
- Use `--view <name>` to run a single capture for fast iteration during development (e.g. `--view now-playing`, `--view replace-prompt`, `--view playback-control`).
- **Always run a `--real` test if you write one.** If you add a `--real-mpv` or `--real-mpv-bitrate` test, run it with `--real` before committing. Fake IPC tests are not sufficient for playback/IPC features — real mpv behavior differs.

## Release Notes And Roadmap Hygiene

- Keep completed roadmap items in `todo.md` marked as done/crossed out instead of deleting them.
- After each release, add a small `CHANGELOG.md` entry.
- Each changelog entry should include a very small testing summary and note any important manual test gap.
- When the user says to commit and/or push, treat that request as a Git-only operation. Do not make further file changes in that step. If a file change is still needed, stop and ask: "I just made my last changes before commit/push. Good to continue?"
- **Every commit MUST update `AGENTS.md`, `TODO.md`, and `CHANGELOG.md`** to reflect the current state. No code commit without corresponding docs updates.

## Release Checklist

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full development and release checklist.

## Near-Term Roadmap

1. Stabilize the promoted 0.0.34 baseline.
2. Server-side safety guard.
3. Audio picker.
4. Better help text / key map cleanup.
5. Split into modules (later, after architecture stabilizes).
6. Build/packaging/Arch PKGBUILD.

Keep those phases separate. Do not bundle threaded refresh, mpv IPC, and playback reporting into one large change.

## Docs Structure (IMPORTANT for merges)

The `docs/` directory was reorganized into release-based subdirectories:

```
docs/
  release-0.0.34/       ← Everything for the 0.0.34 IPC Features release
    release-plan.md
    implementation-plan.md
    implementation-report.md
    manual-testing-results.md
    retest-checklist.md
    claude-didn't-listen.md
    screenshot-analysis.md
  future-release/       ← Planning docs for next release (subject to change)
    release-plan.md
    code-split-analysis.md
    test-harness-analysis.md
  screenshots/          ← 10 SVG screenshots referenced by README
  themes/               ← 23 SVG theme gallery images
```

**OLD directories are GONE:** `docs/planning/`, `docs/plans/`, `docs/reports/`, `docs/manual-testing-results/` — deleted.

**MERGE WARNING:** If another agent still has the old `docs/planning/`, `docs/plans/`, `docs/reports/`, or `docs/manual-testing-results/` directories in their branch, merging will conflict. Before merging:
1. The other agent must rebase on top of the current `ipc-features` HEAD.
2. OR: manually move their files to the correct `docs/release-0.0.34/` or `docs/future-release/` location and delete the old directories.

**Do NOT re-create the old directory structure.** All new release docs go into `docs/release-X.Y.Z/` (or `docs/future-release/` for speculative planning).

---

## Current Playback / IPC Status

- mpv IPC is active: `PlaybackManager` connects to mpv via `--input-ipc-server` Unix socket.
- IPC provides: `ipc_get_property`, `ipc_set_property`, `ipc_command`, `toggle_pause`, `seek_to`, `seek_relative`, `loadfile_replace`, `set_track`, `stop_via_ipc`.
- `stop_active()` tries IPC `stop` first, falls back to `terminate()`.
- `position_ticks()` uses IPC `time-pos` first, falls back to wall-clock estimation.
- Periodic progress reporter sends Jellyfin `/Sessions/Playing/Progress` every 5s via IPC.
- `playback_payload()` reads `pause` state from IPC.
- Bottom status bar shows live playback state: `np: <title> – <MM:SS>`.
- Each playback writes a private log to `~/.cache/jbrowse/mpv.out-YYYYMMDD-HHMMSS-ffffff`.
- `ENABLE_COMMAND_PALETTE = False` set as class attribute on `BrowseApp` to prevent Textual from intercepting Ctrl+P.
- Now Playing page: backspace/q returns to `previous_page` (not hardcoded browser).
- Now Playing page: Ctrl+B shows 3-second quality flash message on-page.
- Now Playing page: web URL overlay (w key) not overwritten by 1s poll timer.
- Info page: Progress line uses regex match to avoid duplicate; 1s auto-update poll when viewing playing item.
- MpV log: line numbers + scroll position indicator (█░ bar + percentage).
- Replace prompt: "Already playing" / "Play this instead?" / "Enter  →  replace" / "Backspace  →  cancel". Panel title: "Replace Playback".
- Ctrl+B quality change: seeks back to saved position after loadfile_replace (1.0s delay thread).
- Replace prompt `n`/backspace: returns to info page (not browser).
- Same-item Enter: pressing Enter on the currently playing item opens Now Playing directly (no replace prompt).
- Ctrl+K from Now Playing: returns to previous_page (info) instead of browser.
- Web URL overlay: render_info() and _render_now_playing() guard on _web_url_visible.
- Info page Progress: regex fixed (Progress\s instead of Progress\s*:); _web_url_visible guard added; 1s auto-update poll with self.refresh().
- Progress display: uses Jellyfin runtime (`item.runtime_ticks`) for total time instead of mpv IPC duration (which can differ during transcoding).
- Help key: F1 removed (Textual intercepts it). Use Ctrl+H (was Ctrl+L/?).
- No F keys policy: F1–F12 all intercepted by Textual, don't use them.
- Harness: 31 captures including all fixed items. `--real-mpv-bitrate` and `--real-mpv-jump` tests pass.
- Completed: All IPC feature phases (1–6) + playback control menu + all manual testing re-test fixes + jump-to-time + real IPC test fixes.
- Bottom bar poll: calls `update_bottom_status()` (page-aware) instead of `bottom_status_text()` directly.
- Now Playing playback-end: returns to `previous_page` (info) instead of hardcoded browser.
- Scroll indicator: text-based `[####----] 42%` (renders in SVG export, unlike `█░` block chars).
- Next: Server-side safety guard, audio picker, help text cleanup, replace prompt wording revision.
