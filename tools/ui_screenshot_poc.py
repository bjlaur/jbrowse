#!/usr/bin/env python3
"""
Harvest a few real-server Textual screenshots for jbrowse UI review.

This is intentionally a proof of concept. It uses the normal jbrowse config,
logs in to Jellyfin, loads cached or fetched items, and saves SVG screenshots
under ./screenshot/.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jbrowse import (  # noqa: E402
    BrowseApp,
    Config,
    JellyfinClient,
    JellyfinError,
    MediaItem,
    Theme,
    UIState,
    default_cfg_path,
    default_item_cache_path,
    default_state_path,
    discover_themes,
    initial_theme,
    load_cfg,
    load_item_cache,
    load_state,
    write_item_cache,
)


def log(message: str) -> None:
    print(f"[screenshot] {message}", file=sys.stderr)


def choose_demo_item(items: list[MediaItem]) -> MediaItem:
    for item in items:
        if item.subtitle_tracks:
            return item

    return items[0]


def load_items(cfg: Config, client: JellyfinClient) -> list[MediaItem]:
    user_id = client.auth.user_id if client.auth is not None else ""
    cache_path = default_item_cache_path()

    start = time.perf_counter()
    log(f"loading item cache: {cache_path}")
    items = load_item_cache(cache_path, cfg, user_id)
    log(f"item cache returned {len(items)} items in {time.perf_counter() - start:.2f}s")

    if items:
        return items

    start = time.perf_counter()
    log("cache miss; fetching Jellyfin items")
    items = client.fetch_items()
    log(f"fetched {len(items)} items in {time.perf_counter() - start:.2f}s")

    start = time.perf_counter()
    log(f"writing item cache: {cache_path}")
    write_item_cache(cache_path, cfg, user_id, items)
    log(f"wrote item cache in {time.perf_counter() - start:.2f}s")
    return items


def screenshot_themes(cfg: Config) -> list[Theme]:
    themes = discover_themes(initial_theme(cfg.style_path))
    by_name = {theme.name: theme for theme in themes}
    preferred = [
        "jbrowse-high-contrast.tcss",
        "jbrowse-batman-high-contrast.tcss",
        "jbrowse-rosewood.tcss",
        "jbrowse-teal-gray.tcss",
    ]

    chosen = [by_name[name] for name in preferred if name in by_name]

    for theme in themes:
        if theme not in chosen:
            chosen.append(theme)

    return chosen


def make_ui_state(cfg: Config, demo_item: MediaItem) -> UIState:
    return UIState(
        view=cfg.sort_mode,
        display_mode=cfg.display_mode,
        sort_desc=cfg.sort_desc,
        selected_item_id=demo_item.id,
        focus="list",
    )


async def settle(app: BrowseApp, pilot, label: str) -> None:
    start = time.perf_counter()
    app.render_items()
    app.update_status()
    await pilot.pause(1.0)
    await pilot.wait_for_scheduled_animations()
    log(f"{label}: settled in {time.perf_counter() - start:.2f}s")


async def capture_screenshot(
    cfg: Config,
    client: JellyfinClient,
    items: list[MediaItem],
    theme: Theme,
    output_dir: Path,
    size: tuple[int, int],
    filename: str,
    view: str,
) -> None:
    capture_start = time.perf_counter()
    log(f"{filename}: starting {view} capture with {theme.name}")

    app_cls = type(
        f"ScreenshotBrowseApp{view.title()}",
        (BrowseApp,),
        {"CSS": theme.tcss},
    )

    demo_item = choose_demo_item(items)
    app = app_cls(
        cfg,
        client,
        items,
        theme.name,
        make_ui_state(cfg, demo_item),
        write_cache_on_start=False,
    )

    async with app.run_test(size=size) as pilot:
        await settle(app, pilot, f"{filename} initial")

        if view == "info":
            app.open_info()
            await settle(app, pilot, f"{filename} info")
        elif view == "subtitles":
            app.open_info()
            await settle(app, pilot, f"{filename} info")
            app.open_subtitle_picker()
            await settle(app, pilot, f"{filename} subtitles")
        elif view == "help":
            app.previous_page = app.page if app.page in {"browser", "info"} else "browser"
            app.page = "help"
            app.render_help()
            await settle(app, pilot, f"{filename} help")

        output_path = output_dir / filename
        export_start = time.perf_counter()
        output_path.write_text(
            app.export_screenshot(title=f"{filename} - {theme.name}"),
            encoding="utf-8",
        )
        log(f"{filename}: exported in {time.perf_counter() - export_start:.2f}s")
        print(f"{filename}: {theme.name}")

    log(f"{filename}: finished in {time.perf_counter() - capture_start:.2f}s")


async def save_screenshots(
    cfg: Config,
    client: JellyfinClient,
    items: list[MediaItem],
    output_dir: Path,
    size: tuple[int, int],
) -> None:
    themes = screenshot_themes(cfg)
    output_dir.mkdir(parents=True, exist_ok=True)

    captures = [
        ("browser.svg", "browser"),
        ("info.svg", "info"),
        ("subtitles.svg", "subtitles"),
        ("help.svg", "help"),
    ]

    for index, (filename, view) in enumerate(captures):
        await capture_screenshot(
            cfg,
            client,
            items,
            themes[index % len(themes)],
            output_dir,
            size,
            filename,
            view,
        )


def parse_size(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        return (int(width), int(height))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("size must look like 120x36") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="POC real-server jbrowse UI screenshot harvester")
    parser.add_argument("--config", help="override config path")
    parser.add_argument("--state", help="override state path")
    parser.add_argument("--output", default="screenshot", help="output directory")
    parser.add_argument("--size", default="120x36", type=parse_size, help="terminal size, e.g. 120x36")
    return parser.parse_args()


def main() -> int:
    total_start = time.perf_counter()
    args = parse_args()

    cfg_path = Path(args.config).expanduser() if args.config else default_cfg_path()
    state_path = Path(args.state).expanduser() if args.state else default_state_path()
    output_dir = Path(args.output).expanduser()

    log(f"loading config: {cfg_path}")
    cfg = load_cfg(cfg_path)
    log(f"loading state: {state_path}")
    state = load_state(state_path)
    client = JellyfinClient(cfg, state)

    try:
        start = time.perf_counter()
        log("logging in to Jellyfin")
        client.login()
        log(f"logged in in {time.perf_counter() - start:.2f}s")
        items = load_items(cfg, client)
    except JellyfinError as exc:
        print(f"Jellyfin error: {exc}", file=sys.stderr)
        return 1

    if not items:
        print("No playable Jellyfin items found.", file=sys.stderr)
        return 1

    asyncio.run(save_screenshots(cfg, client, items, output_dir, args.size))

    print(f"Saved screenshots to {output_dir}")
    log(f"finished all screenshots in {time.perf_counter() - total_start:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
