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

Avoid accidentally adding these before their planned feature work:

```text
input-ipc-server
[player]
```

These strings may become valid later for mpv IPC or player config.

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

## Current Playback Debugging Handoff

- The current background-playback cleanup work is uncommitted. It adds `Ctrl+K` to stop mpv, a deliberate two-step quit, info-panel `Progress`, registered Jellyfin mutation endpoints, and timestamped playback diagnostics.
- The developer manually tried both stopping mpv directly with `Ctrl+C` and `Ctrl+K`; the info-panel `Progress` did not update afterward. Do not assume Jellyfin playback reporting works in normal use.
- Each new playback writes a private, unredacted log to `~/.cache/jbrowse/mpv.out-YYYYMMDD-HHMMSS-ffffff`. It records the exact mpv command, mpv output/exit code, and each Jellyfin start/progress/stopped report result. Do not print or commit its contents because it can contain stream credentials.
- Next debugging step: reproduce one real playback, inspect the newest local log manually for report failures or return codes, then trace why accepted reports are not reflected in Jellyfin. Keep this separate from mpv IPC work.
