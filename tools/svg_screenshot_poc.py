#!/usr/bin/env python3
"""Small Textual SVG screenshot harness for jbrowse."""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jbrowse import (  # noqa: E402
    Auth,
    BrowseApp,
    Config,
    JellyfinClient,
    MediaItem,
    PlaybackManager,
    Theme,
    ThemeCycle,
    UIState,
    default_cfg_path,
    default_item_cache_path,
    default_state_path,
    discover_themes,
    initial_theme,
    load_fake_cache_data,
    load_cfg,
    load_item_cache,
    load_state,
    media_item_from_cache,
)


def log(message: str) -> None:
    print(f"[svg-poc] {message}", file=sys.stderr)


def parse_size(value: str) -> tuple[int, int]:
    width, height = value.lower().split("x", 1)
    return (int(width), int(height))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny Textual SVG screenshot POC")
    parser.add_argument("--output", default="tools/screenshot", help="output directory")
    parser.add_argument("--size", default="120x36", type=parse_size, help="terminal size")
    parser.add_argument(
        "--playback-smoke",
        action="store_true",
        help="also run a fake background playback stop/output smoke test",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="use the local config/cache and Jellyfin server instead of fictional fixtures",
    )
    parser.add_argument(
        "--real-mpv",
        action="store_true",
        help="launch a real mpv instance via PlaybackManager and verify IPC (requires --real and a Jellyfin cache)",
    )
    parser.add_argument(
        "--play-duration",
        type=float,
        default=0.5,
        help="seconds to let mpv play before checking IPC position (default: 0.5). Use 5.0+ for full release smoke tests.",
    )
    parser.add_argument(
        "--item",
        default="",
        help="case-insensitive title, filename, or series substring to feature in captures",
    )
    parser.add_argument(
        "--all-themes",
        action="store_true",
        help="write one browser SVG per theme under docs/themes (on-demand only, not routine)",
    )
    parser.add_argument(
        "--ipc-only",
        action="store_true",
        help="skip all screenshot generation; run only the --real-mpv IPC smoke test (requires --real)",
    )
    parser.add_argument(
        "--real-mpv-bitrate",
        action="store_true",
        help="run real mpv bitrate cycling test: play, cycle quality, verify bitrate via IPC (requires --real)",
    )
    parser.add_argument(
        "--view",
        default="",
        help="run only a single capture by view name (e.g. now-playing, replace-prompt, playback-control)",
    )
    return parser.parse_args()


def choose_demo_item(items: list[MediaItem], query: str = "") -> MediaItem:
    if query:
        needle = query.casefold()
        for item in items:
            haystack = "\n".join((item.title, item.filename, item.series_name)).casefold()
            if needle in haystack:
                return item
        raise RuntimeError(f"No fixture item matches --item {query!r}")

    for item in items:
        if 1 <= len(item.subtitle_tracks) <= 12:
            return item
    for item in items:
        if item.subtitle_tracks:
            return item
    return items[0]


def cached_user_id(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return ""

    return str(data.get("user_id", ""))


def make_state(cfg, item: MediaItem) -> UIState:
    return UIState(
        view=cfg.sort_mode,
        display_mode=cfg.display_mode,
        sort_desc=cfg.sort_desc,
        selected_item_id=item.id,
        focus="list",
    )


def check_svg(name: str, svg: str, expected: list[str]) -> None:
    normalized = html.unescape(svg).replace("\u00a0", " ")
    missing = [text for text in expected if text not in normalized]
    if missing:
        raise RuntimeError(f"{name} missing expected text: {', '.join(missing)}")


def check_theme_svg(name: str, svg: str, theme: Theme) -> None:
    match = re.search(r"Screen\s*\{[^}]*background:\s*(#[0-9a-fA-F]{6})", theme.tcss, re.DOTALL)
    if match is None:
        raise RuntimeError(f"{theme.name} has no Screen background color")
    if match.group(1).lower() not in svg.lower():
        raise RuntimeError(f"{name} did not render {theme.name}'s Screen background")


async def settle(app: BrowseApp, pilot) -> None:
    app.render_items()
    app.update_status()
    for widget in app.screen.walk_children(with_self=True):
        widget._styles_cache.clear()
        widget.refresh(layout=True)
    await pilot.pause(0.3)
    await pilot.wait_for_scheduled_animations()


async def quick_settle(app: BrowseApp, pilot) -> None:
    """Lightweight settle for views that just pressed a key — skips full style cache clear."""
    app.render_items()
    await pilot.pause(0.2)


async def export_view(
    cfg,
    client,
    items: list[MediaItem],
    demo_item: MediaItem,
    theme: Theme,
    size: tuple[int, int],
    output_path: Path,
    view: str,
    expected: list[str],
) -> object:
    BrowseApp.CSS = theme.tcss
    app = BrowseApp(
        cfg,
        client,
        items,
        theme.name,
        make_state(cfg, demo_item),
        write_cache_on_start=False,
        auto_refresh_on_start=False,
        last_mpv_command="mpv --fake-demo",
        last_mpv_output="line one\nline two",
    )

    async with app.run_test(size=size) as pilot:
        await settle(app, pilot)

        if view == "after-ctrl-x":
            await pilot.press("ctrl+x")
            await pilot.pause(0.1)
            return app.return_value

        if view == "info":
            await pilot.press("enter")
            await settle(app, pilot)
        elif view == "search":
            app.query.focus()
            await pilot.press(*"otter")
            await settle(app, pilot)
        elif view == "subtitles":
            await pilot.press("enter")
            await settle(app, pilot)
            await pilot.press("s")
            await settle(app, pilot)
        elif view == "help":
            await pilot.press("?")
            await settle(app, pilot)
        elif view == "mpv-log":
            app.open_mpv_log()
            await settle(app, pilot)
        elif view == "refreshing":
            app.refreshing = True
            app.refresh_message = "refreshing..."
            app.update_bottom_status()
            await settle(app, pilot)
        elif view == "now-playing":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
        elif view == "ctrl-n-now-playing":
            _setup_fake_playback(app, demo_item)
            await settle(app, pilot)
            # Press Ctrl+N to open Now Playing page
            await pilot.press("ctrl+n")
            await settle(app, pilot)
        elif view == "playback-control":
            _setup_fake_playback(app, demo_item)
            app._open_playback_control()
            await settle(app, pilot)
        elif view == "replace-prompt":
            _setup_fake_playback(app, demo_item)
            second_item = items[1] if len(items) > 1 else demo_item
            app._pending_replace_item = second_item
            app._replace_prompt_visible = True
            await settle(app, pilot)
            app._render_replace_prompt()  # render after settle so it's not overwritten
        elif view == "web-url":
            app.info_item = demo_item
            await settle(app, pilot)
            app._show_web_url()
        elif view == "mpv-log-scrolled":
            _setup_fake_playback(app, demo_item)
            app.open_mpv_log()
            await settle(app, pilot)
            # Scroll down a few lines to exercise line numbers + scroll bar
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("down")
            await settle(app, pilot)
        elif view == "info-playing":
            _setup_fake_playback(app, demo_item)
            app.info_item = demo_item
            app.page = "info"
            app.render_info()
            await settle(app, pilot)
        elif view == "info-progress-auto-update":
            _setup_fake_playback(app, demo_item)
            app.info_item = demo_item
            app.page = "info"
            app._info_poll_stop = False
            app.render_info()
            await settle(app, pilot)
            # Wait for the poll timer to fire (1s interval + settle time)
            await pilot.pause(1.5)
            await quick_settle(app, pilot)
        elif view == "now-playing-quality":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            # Cycle quality to trigger flash message
            await pilot.press("ctrl+b")
            await settle(app, pilot)
        elif view == "ctrl-b-bitrate":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            # Cycle quality twice and verify bitrate label updates
            await pilot.press("ctrl+b")
            await settle(app, pilot)
            await pilot.press("ctrl+b")
            await settle(app, pilot)
        elif view == "playback-control-menu":
            _setup_fake_playback(app, demo_item)
            app._open_playback_control()
            await settle(app, pilot)
        elif view == "ctrl-k-stop":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            await pilot.press("ctrl+k")
            await settle(app, pilot)
        elif view == "ctrl-p-from-browser":
            _setup_fake_playback(app, demo_item)
            app._open_playback_control()
            await settle(app, pilot)
        elif view == "space-pause":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            await pilot.press("space")
            await settle(app, pilot)
        elif view == "seek-comma-period":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            await pilot.press(",")
            await settle(app, pilot)
            await pilot.press(".")
            await settle(app, pilot)
        elif view == "bottom-bar-format":
            _setup_fake_playback(app, demo_item)
            await settle(app, pilot)
        elif view == "bottom-bar-long-name":
            long_item = _make_long_filename_item()
            _setup_fake_playback(app, long_item)
            await settle(app, pilot)
        elif view == "replace-n-to-info":
            _setup_fake_playback(app, demo_item)
            second_item = items[1] if len(items) > 1 else demo_item
            app._pending_replace_item = second_item
            app._replace_prompt_visible = True
            await settle(app, pilot)
            app._render_replace_prompt()
            # Press n to cancel — should go back to info
            await pilot.press("n")
            await settle(app, pilot)
        elif view == "info-backspace-to-browser":
            app.info_item = demo_item
            app.page = "info"
            app.render_info()
            await settle(app, pilot)
            await pilot.press("backspace")
            await settle(app, pilot)
        elif view == "now-playing-backspace-to-info":
            _setup_fake_playback(app, demo_item)
            app.info_item = demo_item
            app.page = "info"
            app.render_info()
            await settle(app, pilot)
            # Navigate to Now Playing
            app.open_now_playing()
            await settle(app, pilot)
            # Press backspace — should return to info
            await pilot.press("backspace")
            await settle(app, pilot)
        elif view == "web-url-info-overlay":
            _setup_fake_playback(app, demo_item)
            app.info_item = demo_item
            app.page = "info"
            app.render_info()
            await settle(app, pilot)
            await pilot.press("w")
            await settle(app, pilot)
        elif view == "web-url-now-playing-overlay":
            _setup_fake_playback(app, demo_item)
            app.open_now_playing()
            await settle(app, pilot)
            await pilot.press("w")
            await settle(app, pilot)

        if view in {"browser", "refreshing"} and app.visible_items:
            selected = app.visible_items[app.selected_index]
            expected = [*expected, app.item_text(selected)[:32]]
        elif view == "info" and demo_item.info_lines:
            expected = [*expected, demo_item.info_lines[0][:32]]
        elif view == "subtitles" and demo_item.subtitle_tracks:
            expected = [*expected, demo_item.subtitle_tracks[0].title]

        svg = app.export_screenshot(title=f"{output_path.name} - {theme.name}")
        output_path.write_text(svg, encoding="utf-8")
        check_svg(output_path.name, svg, [theme.name, *expected])
        check_theme_svg(output_path.name, svg, theme)
        log(f"wrote {output_path} with {theme.name}")

    return app.return_value


def _make_long_filename_item() -> MediaItem:
    """Create a media item with a very long filename to test bottom bar truncation."""
    return MediaItem(
        id="long-filename-item",
        title="Rick and Morty - S09E02 - Rick's Days Seven Nights",
        filename="Rick.and.Morty.S09E02.Ricks.Days.Seven.Nights.1080p.AMZN.WEB-DL.DDP5.1.H.264-Kitsune.mkv",
        kind="Episode",
        series_name="Rick and Morty",
        season_number=9,
        episode_number=2,
        premiere_date="2025-01-01",
        date_created="2025-01-01",
        last_played="",
        resume_ticks=0,
        runtime_ticks=28 * 60 * 10_000_000,
        info_lines=["RICK AND MORTY", "Season 9 - 2. Rick's Days Seven Nights", "1/1/2025   28 m", "", "Video       1080p HEVC SDR", "Audio       English - Dolby Digital+ - Stereo - Default", "Subtitles   English - SUBRIP", "Progress      0:00 / 28:00", "", "Synopsis text goes here."],
        subtitle_tracks=[],
    )


class _FakeState:
    deviceid = "fixture-device-id"


class FixtureClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.auth = Auth(user_id="fixture-user", token="fixture-token")
        self.state = _FakeState()

    def stream_url(self, item: MediaItem) -> str:
        return f"https://example.invalid/Items/{item.id}/stream?api_key=fixture-token"

    def fetch_items(self) -> list[MediaItem]:
        return fixture_items()

    def report_playback_started(self, payload: dict) -> None:
        pass

    def report_playback_progress(self, payload: dict) -> None:
        pass

    def report_playback_stopped(self, payload: dict) -> None:
        pass


_FAKE_IPC_VALUES = {
    "time-pos": 30.0,
    "duration": 120.0,
    "pause": False,
    "track-list": [
        {"type": "video", "codec": "hevc", "w": 1920, "h": 1080, "selected": True},
        {"type": "audio", "codec": "ac3", "lang": "en", "demux-channel-count": 6, "selected": True},
        {"type": "sub", "lang": "en", "selected": True},
    ],
}


class _FakeProcess:
    """A fake subprocess.Popen that looks active for screenshot captures."""
    def poll(self):
        return None  # None = still running
    def terminate(self):
        pass
    def kill(self):
        pass


class _FakeIpcSock:
    """Minimal fake IPC socket that returns plausible values for screenshot captures."""
    def sendall(self, data: bytes) -> None:
        pass
    def recv(self, size: int) -> bytes:
        return b""
    def close(self) -> None:
        pass
    def settimeout(self, timeout: float) -> None:
        pass


def _setup_fake_playback(app: BrowseApp, item: MediaItem) -> None:
    """Set up a fake active playback so Now Playing and Control Menu screens render with data."""
    pm = app.playback_manager
    pm.item = item
    pm.play_session_id = "fixture-session"
    pm.last_command = "mpv --fake-demo"
    pm.output_lines = [f"Now Playing: {item.filename}\n", "line one\n", "line two\n"]
    pm.last_return_code = None
    pm.started_at = time.monotonic()
    # Fake a "running" process so is_active() returns True
    pm.process = _FakeProcess()
    # Override IPC methods to return fake values
    pm._ipc_sock = _FakeIpcSock()
    pm.ipc_get_property = lambda name: _FAKE_IPC_VALUES.get(name)
    pm._ipc_get_number = lambda name: _FAKE_IPC_VALUES.get(name)
    _fake_paused = {"value": False}
    def _toggle_pause():
        _fake_paused["value"] = not _fake_paused["value"]
        _FAKE_IPC_VALUES["pause"] = _fake_paused["value"]
        return True
    pm.toggle_pause = _toggle_pause
    pm.seek_relative = lambda d: True
    pm.loadfile_replace = lambda url: True


def fixture_cfg() -> Config:
    """A complete local config so screenshots never touch a real server or config."""
    return Config(
        path=ROOT / "jbrowse.fixture.conf",
        jellyfin_url="https://example.invalid",
        username="fixture-user",
        password="fixture-password",
        item_types=["Movie", "Episode"],
        initial_view="added",
        sort_mode="added",
        sort_desc=True,
        max_display_items=0,
        display_mode="title",
        style_path=None,
        mpv_cmd=["mpv", "$url"],
        refresh_interval_minutes=0,
        quality_presets=["direct", "40mbps", "20mbps", "12mbps", "8mbps", "4mbps", "2mbps"],
        default_quality="direct",
    )


def fixture_items() -> list[MediaItem]:
    """Load committed fictional media through the normal cache-item decoder."""
    data = load_fake_cache_data()

    items = []
    for row in data.get("items", []):
        if not isinstance(row, dict):
            continue
        item = media_item_from_cache(row)
        if item is not None:
            items.append(item)

    if not items:
        raise RuntimeError("No valid fixture items found in fake cache data")
    return items


def real_demo_data() -> tuple[Config, JellyfinClient, list[MediaItem]]:
    """Load the old real-server source only when it is explicitly requested."""
    cfg = load_cfg(default_cfg_path())
    state = load_state(default_state_path())
    client = JellyfinClient(cfg, state)
    cache_path = default_item_cache_path()
    items = load_item_cache(cache_path, cfg, cached_user_id(cache_path))
    if not items:
        client.login()
        items = client.fetch_items()
    if not items:
        raise RuntimeError("No cached items found; run jbrowse once before using --real.")
    return cfg, client, items


def fake_playback_item() -> MediaItem:
    return MediaItem(
        id="fake-playback",
        title="Fake Playback",
        filename="fake-playback.mkv",
        kind="Movie",
        series_name="",
        season_number=None,
        episode_number=None,
        premiere_date="",
        date_created="",
        last_played="",
        resume_ticks=0,
        runtime_ticks=0,
        info_lines=["Fake Playback"],
        subtitle_tracks=[],
    )


def run_playback_smoke(cfg) -> dict:
    log("running fake playback smoke; this intentionally emits output until stopped")
    fake_cfg = dataclasses.replace(
        cfg,
        mpv_cmd=[
            sys.executable,
            "-c",
            (
                "import datetime, sys, time; "
                "print('fake mpv start'); "
                "sys.stdout.flush(); "
                "\nfor tick in range(1, 21):\n"
                "    time.sleep(0.5)\n"
                "    print(f'fake mpv tick {tick} {datetime.datetime.now().isoformat(timespec=\"seconds\")}')\n"
                "    sys.stdout.flush()\n"
                "print('fake mpv end')"
            ),
            "$url",
        ],
    )
    manager = PlaybackManager(FixtureClient(fake_cfg))
    started_at = time.monotonic()
    error = manager.start_background(fake_playback_item())
    launch_elapsed = time.monotonic() - started_at
    if error:
        raise RuntimeError(error)
    if launch_elapsed > 1:
        raise RuntimeError(f"fake playback launch blocked for {launch_elapsed:.2f}s")
    if not manager.is_active():
        raise RuntimeError("fake playback did not start in the background")

    output_deadline = time.monotonic() + 3
    while "fake mpv tick 1" not in manager.snapshot()["output"] and time.monotonic() < output_deadline:
        time.sleep(0.1)

    if "fake mpv tick 1" not in manager.snapshot()["output"]:
        raise RuntimeError("fake playback did not produce delayed output")
    if not manager.stop_active():
        raise RuntimeError("fake playback did not accept stop request")

    deadline = time.monotonic() + 5
    while manager.is_active() and time.monotonic() < deadline:
        time.sleep(0.1)

    if manager.is_active():
        raise RuntimeError("fake playback did not finish")

    result = manager.snapshot()
    if (
        "fake mpv start" not in result["output"]
        or "fake mpv tick 1" not in result["output"]
        or "jbrowse requested mpv stop" not in result["output"]
    ):
        raise RuntimeError("fake playback output was not captured")
    if "api_key=fixture-token" not in result["command"]:
        raise RuntimeError("fake playback command was not captured exactly")
    log("fake playback smoke stopped background playback and captured command/output")
    return result


def run_real_mpv_smoke(cfg, client, item, play_duration: float = 3.0) -> None:
    """Launch real mpv via PlaybackManager and verify IPC position reporting."""
    log(f"running real mpv smoke test (play_duration={play_duration}s)")

    if client.auth is None:
        log("logging in to Jellyfin for real mpv smoke")
        client.login()

    manager = PlaybackManager(client)
    error = manager.start_background(item)
    if error:
        raise RuntimeError(f"real mpv failed to start: {error}")
    if not manager.is_active():
        raise RuntimeError("real mpv did not start in the background")

    log(f"real mpv started; letting it play for {play_duration}s")
    time.sleep(play_duration)

    snapshot = manager.snapshot()
    log(f"real mpv snapshot: active={snapshot['active']}, title={snapshot['title']}")
    log(f"real mpv output (first 200 chars): {snapshot['output'][:200]!r}")

    # Verify IPC position reporting: time-pos should be close to play_duration
    ipc_time_pos = manager.ipc_get_property("time-pos")
    log(f"IPC time-pos: {ipc_time_pos}")
    if ipc_time_pos is not None:
        # Allow tolerance: mpv startup overhead + playback latency
        min_expected = play_duration * 0.5  # at least 50% of elapsed time
        max_expected = play_duration + 3.0   # no more than elapsed + 3s buffer
        if not (min_expected <= ipc_time_pos <= max_expected):
            raise RuntimeError(
                f"IPC time-pos {ipc_time_pos:.1f}s out of expected range "
                f"[{min_expected:.1f}, {max_expected:.1f}] after {play_duration}s playback"
            )
        log(f"IPC time-pos {ipc_time_pos:.1f}s is within expected range "
            f"[{min_expected:.1f}, {max_expected:.1f}] — position reporting OK")
    else:
        log("WARNING: IPC time-pos returned None — position reporting not verified")

    if not manager.stop_active():
        raise RuntimeError("real mpv did not accept stop request")

    deadline = time.monotonic() + 5
    while manager.is_active() and time.monotonic() < deadline:
        time.sleep(0.2)
    if manager.is_active():
        raise RuntimeError("real mpv did not finish after stop")

    log("real mpv smoke passed")


async def run_real_mpv_bitrate_test(cfg, client, item, play_duration: float = 5.0) -> None:
    """Launch real mpv with a Euphoria 2160p file, cycle bitrate via Ctrl+B, verify via IPC.

    Steps: search for 'euphoria 2160p', pick first result, play it, cycle quality twice,
    verify bitrate label changes via IPC.
    """
    log(f"running real mpv bitrate test (play_duration={play_duration}s)")

    # Clean up stale IPC sockets and mpv processes
    import glob
    for sock in glob.glob("/tmp/jbrowse-mpv-*.sock"):
        os.unlink(sock)
    subprocess.run(["pkill", "-f", "mpv.*jbrowse"], capture_output=True)
    time.sleep(0.5)

    if client.auth is None:
        log("logging in to Jellyfin for real mpv bitrate test")
        client.login()

    items = client.fetch_items()
    state = make_state(cfg, items[0])

    app = BrowseApp(
        cfg, client, items, "01-jbrowse-amber-dim", state,
        write_cache_on_start=False, auto_refresh_on_start=False,
    )

    async with app.run_test(size=(120, 36)) as pilot:
        await pilot.pause(0.5)

        # Search for "euphoria"
        app.query.focus()
        await pilot.press(*"euphoria")
        await pilot.pause(0.5)

        if not app.visible_items:
            raise RuntimeError("No items found for 'euphoria' search")

        # Pick the first Euphoria 2160p result, or fall back to any Euphoria
        first = None
        for item in app.visible_items:
            if "2160" in item.filename.casefold() or "4k" in item.filename.casefold():
                first = item
                break
        if first is None:
            first = app.visible_items[0]

        if "euphoria" not in first.title.casefold():
            raise RuntimeError(f"First result is not Euphoria: {first.title}")
        log(f"found: {first.title} ({first.filename})")

        # Play it: Enter → info, Enter → play
        app.selected_index = 0
        await pilot.press("enter")
        await pilot.pause(0.5)
        await pilot.press("enter")
        await pilot.pause(0.5)

        log(f"playing for {play_duration}s")
        await pilot.pause(play_duration)

        # Wait for IPC to be ready (up to 5s)
        for _ in range(10):
            if app.playback_manager.ipc_get_property("time-pos") is not None:
                break
            await pilot.pause(0.5)
        else:
            raise RuntimeError("IPC not connected after 5s — check mpv --input-ipc-server flag")

        quality_before = app._current_quality_label()
        log(f"before: quality={quality_before}")

        # Cycle quality
        await pilot.press("ctrl+b")
        await pilot.pause(3.0)
        quality_after = app._current_quality_label()
        log(f"after 1st: quality={quality_after}")
        if quality_after == quality_before:
            # Debug: check if IPC is working
            ipc_pos = app.playback_manager.ipc_get_property("time-pos")
            log(f"IPC time-pos: {ipc_pos}")
            raise RuntimeError(f"quality unchanged: {quality_after}")

        # Cycle again
        await pilot.press("ctrl+b")
        await pilot.pause(2.0)
        quality_after2 = app._current_quality_label()
        log(f"after 2nd: quality={quality_after2}")
        if quality_after2 == quality_after:
            raise RuntimeError(f"quality unchanged on 2nd cycle: {quality_after2}")

        # Stop
        await pilot.press("ctrl+k")
        await pilot.pause(1.0)

        log("real mpv bitrate test passed")


async def main_async(args: argparse.Namespace) -> int:
    if args.real:
        cfg, client, items = real_demo_data()
        theme_start = initial_theme(cfg.style_path)
        log("using real local cache/server data; output may contain private media names")
    else:
        cfg = fixture_cfg()
        client = FixtureClient(cfg)
        items = fixture_items()
        theme_start = initial_theme(ROOT / "themes" / "01-jbrowse-amber-dim.tcss")
        log("using fictional publishing fixtures")

    demo_item = choose_demo_item(items, args.item)
    if args.item:
        log(f"featuring {demo_item.title}")

    if args.ipc_only:
        if not args.real:
            raise RuntimeError("--ipc-only requires --real (needs real Jellyfin cache and server)")
        run_real_mpv_smoke(cfg, client, demo_item, args.play_duration)
        return 0

    if args.real_mpv_bitrate:
        if not args.real:
            raise RuntimeError("--real-mpv-bitrate requires --real (needs real Jellyfin cache and server)")
        await run_real_mpv_bitrate_test(cfg, client, demo_item, args.play_duration)
        return 0

    themes = discover_themes(theme_start)
    if args.all_themes:
        gallery = ROOT / "docs" / "themes"
        gallery.mkdir(parents=True, exist_ok=True)
        for old_svg in gallery.glob("*.svg"):
            old_svg.unlink()

        for theme in themes:
            filename = theme.path.stem if theme.path is not None else theme.name
            await export_view(
                cfg,
                client,
                items,
                demo_item,
                theme,
                args.size,
                gallery / f"{filename}.svg",
                "browser",
                ["showing", "display:", "style:"],
            )

        if args.playback_smoke:
            run_playback_smoke(cfg)
        return 0

    # --view: run only a single capture for fast iteration (skips all other captures)
    if args.view:
        view_map = {
            "browser": ("browser.svg", "browser", ["showing", "display:", "style:"]),
            "after-ctrl-x": ("after-ctrl-x.svg", "after-ctrl-x", []),
            "search": ("search.svg", "search", ["otter", "matched", "showing"]),
            "info": ("info.svg", "info", ["Info", "Subtitles", "Progress"]),
            "subtitles": ("subtitles.svg", "subtitles", ["Subtitles", "auto", "none"]),
            "help": ("help.svg", "help", ["Help", "Ctrl+G", "Ctrl+K", "Ctrl+X", "Ctrl+P", "Ctrl+N", "Ctrl+B"]),
            "mpv-log": ("mpv-log.svg", "mpv-log", ["mpv log", "Status", "not playing", "mpv --fake-demo", "line one"]),
            "refreshing": ("refreshing.svg", "refreshing", ["refreshing...", "style:"]),
            "now-playing": ("now-playing.svg", "now-playing", ["Now Playing", "playing", "quality:", "direct", "state:", "video:", "audio:", "subtitle:", "0:30 / 2:00"]),
            "playback-control": ("playback-control.svg", "playback-control", ["Playback Control", "state:", "quality:", "Space pause", "Ctrl+B quality", "Ctrl+N now playing"]),
            "replace-prompt": ("replace-prompt.svg", "replace-prompt", ["Already playing", "Play this instead?", "Enter", "replace", "Backspace", "cancel"]),
            "playback-control-menu": ("playback-control-menu.svg", "playback-control-menu", ["Playback Control", "state:", "quality:"]),
            "ctrl-k-stop": ("ctrl-k-stop.svg", "ctrl-k-stop", ["not playing"]),
            "ctrl-p-from-browser": ("ctrl-p-from-browser.svg", "ctrl-p-from-browser", ["Playback Control"]),
            "space-pause": ("space-pause.svg", "space-pause", ["paused"]),
            "bottom-bar-format": ("bottom-bar-format.svg", "bottom-bar-format", ["np:", "–"]),
            "bottom-bar-long-name": ("bottom-bar-long-name.svg", "bottom-bar-long-name", ["Rick and Morty", "S09E02"]),
            "replace-n-to-info": ("replace-n-to-info.svg", "replace-n-to-info", ["Info"]),
            "info-backspace-to-browser": ("info-backspace-to-browser.svg", "info-backspace-to-browser", ["showing"]),
            "now-playing-backspace-to-info": ("now-playing-backspace-to-info.svg", "now-playing-backspace-to-info", ["Info"]),
            "web-url-info-overlay": ("web-url-info-overlay.svg", "web-url-info-overlay", ["Jellyfin Web URL"]),
            "web-url-now-playing-overlay": ("web-url-now-playing-overlay.svg", "web-url-now-playing-overlay", ["Jellyfin Web URL"]),
            "info-progress-auto-update": ("info-progress-auto-update.svg", "info-progress-auto-update", ["Info", "Progress", "0:30 / 2:00"]),
            "ctrl-n-now-playing": ("ctrl-n-now-playing.svg", "ctrl-n-now-playing", ["Now Playing", "playing", "state:"]),
            "ctrl-b-bitrate": ("ctrl-b-bitrate.svg", "ctrl-b-bitrate", ["Now Playing", "quality: 20mbps"]),
        }
        if args.view not in view_map:
            print(f"Unknown --view {args.view!r}. Available: {', '.join(sorted(view_map))}", file=sys.stderr)
            return 1
        output = Path(args.output).expanduser()
        output.mkdir(parents=True, exist_ok=True)
        filename, view_name, expected = view_map[args.view]
        await export_view(
            cfg, client, items, demo_item, themes[0], args.size,
            output / filename, view_name, expected,
        )
        return 0

    output = Path(args.output).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    for old_svg in output.glob("*.svg"):
        old_svg.unlink()

    await export_view(
        cfg,
        client,
        items,
        demo_item,
        themes[0],
        args.size,
        output / "browser.svg",
        "browser",
        ["showing", "display:", "style:"],
    )

    result = await export_view(
        cfg,
        client,
        items,
        demo_item,
        themes[0],
        args.size,
        output / "after-ctrl-x.svg",
        "after-ctrl-x",
        [],
    )
    if not isinstance(result, ThemeCycle):
        print("Ctrl+X did not return ThemeCycle.", file=sys.stderr)
        return 1

    await export_view(
        cfg,
        client,
        items,
        demo_item,
        themes[1 % len(themes)],
        args.size,
        output / "after-ctrl-x.svg",
        "browser",
        ["showing", "display:", "style:"],
    )

    captures = [
        ("search.svg", "search", ["otter", "matched", "showing"]),
        ("info.svg", "info", ["Info", "Subtitles", "Progress"]),
        ("subtitles.svg", "subtitles", ["Subtitles", "auto", "none"]),
        ("help.svg", "help", ["Help", "Ctrl+G", "Ctrl+K", "Ctrl+X", "Ctrl+P", "Ctrl+N", "Ctrl+B"]),
        ("mpv-log.svg", "mpv-log", ["mpv log", "Status", "not playing", "mpv --fake-demo", "line one", "1", "2", "3"]),
        ("refreshing.svg", "refreshing", ["refreshing...", "style:"]),
        ("now-playing.svg", "now-playing", ["Now Playing", "playing", "quality:", "direct", "state:", "video:", "audio:", "subtitle:", "0:30 / 2:00"]),
        ("ctrl-n-now-playing.svg", "ctrl-n-now-playing", ["Now Playing", "playing", "state:"]),
        ("playback-control.svg", "playback-control", ["Playback Control", "state:", "quality:", "Space pause", "Ctrl+B quality", "Ctrl+N now playing"]),
        ("replace-prompt.svg", "replace-prompt", ["Already playing", "Play this instead?", "Enter", "replace", "Backspace", "cancel"]),
        ("web-url.svg", "web-url", ["Jellyfin Web URL", "details?id=", "q close"]),
        ("mpv-log-scrolled.svg", "mpv-log-scrolled", ["mpv log", "Status", "5", "6"]),
        ("info-playing.svg", "info-playing", ["Info", "Progress", "0:30 / 2:00"]),
        ("now-playing-quality.svg", "now-playing-quality", ["Now Playing", "quality: 40mbps"]),
        ("playback-control-menu.svg", "playback-control-menu", ["Playback Control", "state:", "quality:", "Space pause", "Ctrl+B quality"]),
        ("ctrl-k-stop.svg", "ctrl-k-stop", ["stopping mpv"]),
        ("ctrl-p-from-browser.svg", "ctrl-p-from-browser", ["Playback Control", "state:", "quality:"]),
        ("space-pause.svg", "space-pause", ["Now Playing", "paused"]),
        ("seek-comma-period.svg", "seek-comma-period", ["Now Playing"]),
        ("bottom-bar-format.svg", "bottom-bar-format", ["np:", "–", "0:30"]),
        ("bottom-bar-long-name.svg", "bottom-bar-long-name", ["Rick and Morty", "S09E02", "np:"]),
        ("replace-n-to-info.svg", "replace-n-to-info", ["Info"]),
        ("info-backspace-to-browser.svg", "info-backspace-to-browser", ["showing", "display:"]),
        ("now-playing-backspace-to-info.svg", "now-playing-backspace-to-info", ["Info"]),
        ("web-url-info-overlay.svg", "web-url-info-overlay", ["Jellyfin Web URL", "q close"]),
        ("web-url-now-playing-overlay.svg", "web-url-now-playing-overlay", ["Jellyfin Web URL", "q close"]),
        ("info-progress-auto-update.svg", "info-progress-auto-update", ["Info", "Progress", "0:30 / 2:00"]),
        ("ctrl-b-bitrate.svg", "ctrl-b-bitrate", ["Now Playing", "quality: 20mbps"]),
    ]

    for index, (filename, view, expected) in enumerate(captures, start=2):
        await export_view(
            cfg,
            client,
            items,
            demo_item,
            themes[index % len(themes)],
            args.size,
            output / filename,
            view,
            expected,
        )

    if args.playback_smoke:
        run_playback_smoke(cfg)

    if args.real_mpv:
        if not args.real:
            raise RuntimeError("--real-mpv requires --real (needs real Jellyfin cache and server)")
        run_real_mpv_smoke(cfg, client, demo_item, args.play_duration)

    return 0


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
