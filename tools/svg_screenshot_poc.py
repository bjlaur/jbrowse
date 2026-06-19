#!/usr/bin/env python3
"""Small Textual SVG screenshot harness for jbrowse."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jbrowse import (  # noqa: E402
    BrowseApp,
    JellyfinClient,
    MediaItem,
    Theme,
    ThemeCycle,
    UIState,
    default_cfg_path,
    default_item_cache_path,
    default_state_path,
    discover_themes,
    initial_theme,
    load_cfg,
    load_item_cache,
    load_state,
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
    return parser.parse_args()


def cached_user_id(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return ""

    return str(data.get("user_id", ""))


def choose_demo_item(items: list[MediaItem]) -> MediaItem:
    for item in items:
        if item.subtitle_tracks:
            return item
    return items[0]


def make_state(cfg, item: MediaItem) -> UIState:
    return UIState(
        view=cfg.sort_mode,
        display_mode=cfg.display_mode,
        sort_desc=cfg.sort_desc,
        selected_item_id=item.id,
        focus="list",
    )


def check_svg(name: str, svg: str, expected: list[str]) -> None:
    missing = [text for text in expected if text not in svg]
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
        elif view == "refreshing":
            app.refreshing = True
            app.refresh_message = "refreshing..."
            app.update_bottom_status()
            await settle(app, pilot)

        svg = app.export_screenshot(title=f"{output_path.name} - {theme.name}")
        check_svg(output_path.name, svg, [theme.name, *expected])
        output_path.write_text(svg, encoding="utf-8")
        log(f"wrote {output_path} with {theme.name}")

    return app.return_value


async def main_async(args: argparse.Namespace) -> int:
    cfg = load_cfg(default_cfg_path())
    state = load_state(default_state_path())
    client = JellyfinClient(cfg, state)
    cache_path = default_item_cache_path()
    items = load_item_cache(cache_path, cfg, cached_user_id(cache_path))
    if not items:
        client.login()
        items = load_item_cache(default_item_cache_path(), cfg, client.auth.user_id if client.auth else "")
    if not items:
        print("No cached items found; run jbrowse once or the real-terminal POC first.", file=sys.stderr)
        return 1

    themes = discover_themes(initial_theme(cfg.style_path))
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
        ["showing", "display:", "style:"],
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
        ["showing", "display:", "style:"],
    )

    captures = [
        ("info.svg", "info", ["Info", "Enter", "subtitles"]),
        ("subtitles.svg", "subtitles", ["Subtitles", "auto", "none"]),
        ("help.svg", "help", ["Help", "Ctrl+X"]),
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

    return 0


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
