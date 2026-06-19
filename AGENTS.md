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
- Local style override: `jbrowse.tcss`; ignored. Named theme files belong under `themes/` and are safe to commit.

## Important Design Decisions

- Do not reintroduce Textual `ListView`/`ListItem` for media rows. The app uses one `Static` widget (`ItemPane`) that renders visible rows only; this is critical for large libraries.
- `Ctrl+I` is not suitable for info because terminals treat it as Tab.
- F2 was rejected as an info key. Current behavior is `Enter` for info and `Shift+Enter` for direct playback.
- No `[player]` config yet. `mpv` playback is intentionally simple, with only the lightweight `[mpv] mpv_cmd` command template.
- Manual refresh is backgrounded. Periodic refresh should be done separately from playback architecture.

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
/Sessions/Playing
[player]
```

These strings may become valid later for mpv IPC, Jellyfin playback reporting, or player config.

## Release Notes And Roadmap Hygiene

- Keep completed roadmap items in `todo.md` marked as done/crossed out instead of deleting them.
- After each release, add a small `CHANGELOG.md` entry.
- Each changelog entry should include a very small testing summary and note any important manual test gap.

## Near-Term Roadmap

1. Stabilize the promoted 0.0.28 baseline.
2. Add periodic refresh/cache refresh options only after manual background refresh feels solid.
3. Introduce a `PlaybackManager` before adding background mpv, mpv IPC, Now Playing, or Jellyfin progress reporting.

Keep those phases separate. Do not bundle threaded refresh, mpv IPC, and playback reporting into one large change.
