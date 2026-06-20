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
        "--item",
        default="",
        help="case-insensitive title, filename, or series substring to feature in captures",
    )
    parser.add_argument(
        "--all-themes",
        action="store_true",
        help="write one browser SVG per theme under docs/themes",
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
    await pilot.pause(1.0)
    await pilot.wait_for_scheduled_animations()


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
            await pilot.pause(0.2)
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
        ("help.svg", "help", ["Help", "Ctrl+G", "Ctrl+K", "Ctrl+X"]),
        ("mpv-log.svg", "mpv-log", ["mpv log", "Status", "not playing", "mpv --fake-demo", "line one"]),
        ("refreshing.svg", "refreshing", ["refreshing...", "style:"]),
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

    return 0


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
