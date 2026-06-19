#!/usr/bin/env python3
"""Small Textual SVG screenshot harness for jbrowse."""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import html
import json
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
    parser.add_argument("--output", default="screenshot", help="output directory")
    parser.add_argument("--size", default="120x36", type=parse_size, help="terminal size")
    parser.add_argument(
        "--playback-smoke",
        action="store_true",
        help="also run a fake 3-second background playback capture smoke test",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="use the local config/cache and Jellyfin server instead of fictional fixtures",
    )
    return parser.parse_args()


def choose_demo_item(items: list[MediaItem]) -> MediaItem:
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


async def settle(app: BrowseApp, pilot) -> None:
    app.render_items()
    app.update_status()
    await pilot.pause(1.0)
    await pilot.wait_for_scheduled_animations()


async def export_view(
    cfg,
    client,
    items: list[MediaItem],
    theme: Theme,
    size: tuple[int, int],
    output_path: Path,
    view: str,
    expected: list[str],
) -> object:
    BrowseApp.CSS = theme.tcss
    demo_item = choose_demo_item(items)
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
            await pilot.pause(0.2)
            return app.return_value

        if view == "info":
            await pilot.press("enter")
            await settle(app, pilot)
        elif view == "subtitles":
            await pilot.press("enter")
            await settle(app, pilot)
            await pilot.press("s")
            await settle(app, pilot)
        elif view == "help":
            await pilot.press("f1")
            await settle(app, pilot)
        elif view == "mpv-log":
            app.open_mpv_log()
            await settle(app, pilot)
        elif view == "refreshing":
            app.refreshing = True
            app.refresh_message = "refreshing..."
            app.update_bottom_status()
            await settle(app, pilot)

        svg = app.export_screenshot(title=f"{output_path.name} - {theme.name}")
        output_path.write_text(svg, encoding="utf-8")
        check_svg(output_path.name, svg, [theme.name, *expected])
        log(f"wrote {output_path} with {theme.name}")

    return app.return_value


class FixtureClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.auth = Auth(user_id="fixture-user", token="fixture-token")

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
        info_lines=["Fake Playback"],
        subtitle_tracks=[],
    )


def run_playback_smoke(cfg) -> dict:
    log("running fake playback smoke; this intentionally emits output for 3 seconds")
    fake_cfg = dataclasses.replace(
        cfg,
        mpv_cmd=[
            sys.executable,
            "-c",
            (
                "import datetime, sys, time; "
                "print('fake mpv start'); "
                "sys.stdout.flush(); "
                "\nfor tick in range(1, 7):\n"
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

    deadline = time.monotonic() + 10
    while manager.is_active() and time.monotonic() < deadline:
        time.sleep(0.1)

    if manager.is_active():
        raise RuntimeError("fake playback did not finish")

    result = manager.snapshot()
    if result["return_code"] != 0:
        raise RuntimeError(f"fake playback returned {result['return_code']}")
    if (
        "fake mpv start" not in result["output"]
        or "fake mpv tick 6" not in result["output"]
        or "fake mpv end" not in result["output"]
    ):
        raise RuntimeError("fake playback output was not captured")
    if "api_key=REDACTED" not in result["command"]:
        raise RuntimeError("fake playback command was not redacted")
    log("fake playback smoke captured command/output")
    return result


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

    themes = discover_themes(theme_start)
    output = Path(args.output).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    for old_svg in output.glob("*.svg"):
        old_svg.unlink()

    await export_view(
        cfg,
        client,
        items,
        themes[0],
        args.size,
        output / "browser.svg",
        "browser",
        ["showing", "display:", "Lorem Ipsum", "Dolor Sit Amet", "style:"],
    )

    result = await export_view(
        cfg,
        client,
        items,
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
        themes[1 % len(themes)],
        args.size,
        output / "after-ctrl-x.svg",
        "browser",
        ["showing", "display:", "Lorem Ipsum", "style:"],
    )

    captures = [
        ("info.svg", "info", ["Info", "LOREM IPSUM", "Japanese", "Subtitles"]),
        ("subtitles.svg", "subtitles", ["Subtitles", "auto", "none", "English SDH"]),
        ("help.svg", "help", ["Help", "Ctrl+G", "Ctrl+X"]),
        ("mpv-log.svg", "mpv-log", ["mpv log", "mpv --fake-demo", "line one"]),
        ("refreshing.svg", "refreshing", ["refreshing...", "style:"]),
    ]
    for index, (filename, view, expected) in enumerate(captures, start=2):
        await export_view(
            cfg,
            client,
            items,
            themes[index % len(themes)],
            args.size,
            output / filename,
            view,
            expected,
        )

    if args.playback_smoke:
        run_playback_smoke(cfg)

    return 0


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
