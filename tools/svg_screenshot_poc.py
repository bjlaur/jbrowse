#!/usr/bin/env python3
"""
Tiny Textual SVG screenshot POC.

Open jbrowse with run_test, export one SVG, press Ctrl+X with the pilot,
open the next theme, then export another SVG.
"""

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
    parser.add_argument("--output", default="screenshot/svg-poc", help="output directory")
    parser.add_argument("--size", default="120x36", type=parse_size, help="terminal size")
    return parser.parse_args()


def cached_user_id(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return ""

    return str(data.get("user_id", ""))


async def run_app(cfg, client, items, theme, size: tuple[int, int], output_path: Path, press_ctrl_x: bool) -> object:
    BrowseApp.CSS = theme.tcss
    app = BrowseApp(
        cfg,
        client,
        items,
        theme.name,
        UIState(view=cfg.sort_mode, display_mode=cfg.display_mode, sort_desc=cfg.sort_desc, focus="list"),
        write_cache_on_start=False,
        auto_refresh_on_start=False,
    )

    async with app.run_test(size=size) as pilot:
        app.render_items()
        app.update_status()
        await pilot.pause(1.0)
        await pilot.wait_for_scheduled_animations()
        output_path.write_text(app.export_screenshot(title=theme.name), encoding="utf-8")
        log(f"wrote {output_path} with {theme.name}")

        if press_ctrl_x:
            await pilot.press("ctrl+x")
            await pilot.pause(0.2)

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

    result = await run_app(cfg, client, items, themes[0], args.size, output / "before.svg", True)
    if not isinstance(result, ThemeCycle):
        print("Ctrl+X did not return ThemeCycle.", file=sys.stderr)
        return 1

    await run_app(cfg, client, items, themes[1 % len(themes)], args.size, output / "after-ctrl-x.svg", False)
    return 0


def main() -> int:
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
