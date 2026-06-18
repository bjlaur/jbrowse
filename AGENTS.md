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
- No `[player]` config yet. `mpv` playback is intentionally simple.
- Manual refresh is currently blocking. Threaded refresh is planned but should be done separately from playback architecture.

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

## Near-Term Roadmap

1. Stabilize the promoted 0.0.24 baseline.
2. Add a subtitle picker, or add threaded refresh if refresh/startup still feels annoying.
3. Later, introduce a `PlaybackManager` before adding background mpv, mpv IPC, Now Playing, or Jellyfin progress reporting.

Keep those phases separate. Do not bundle subtitle selection, threaded refresh, mpv IPC, and playback reporting into one large change.
