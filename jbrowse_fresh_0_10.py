#!/usr/bin/env python3
"""
jbrowse - tiny Jellyfin TUI launcher for mpv

Config:
  1. jbrowse.conf next to this script
  2. ~/.config/jbrowse/jbrowse.conf

State:
  1. jbrowse.state next to this script, if it exists
  2. ~/.cache/jbrowse/jbrowse.state

Playback:
  mpv --hwdec=auto --force-media-title="$title" "$url"

Dependencies:
  pip install textual requests
"""

from __future__ import annotations

import argparse
import configparser
import dataclasses
import datetime as dt
import re
import secrets
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("Missing dependency: requests\nInstall with: pip install requests", file=sys.stderr)
    raise SystemExit(1)

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Input, Label, ListItem, ListView
except ImportError:
    print("Missing dependency: textual\nInstall with: pip install textual", file=sys.stderr)
    raise SystemExit(1)


APP_NAME = "jbrowse"
CLIENT_NAME = "jbrowse"
CLIENT_VERSION = "0.10"
TICKS_PER_SECOND = 10_000_000
DEFAULT_VISIBLE_ITEMS = 300


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def default_cfg_path() -> Path:
    local = script_dir() / "jbrowse.conf"
    if local.exists():
        return local

    fallback = Path.home() / ".config" / APP_NAME / "jbrowse.conf"
    if fallback.exists():
        return fallback

    return local


def default_state_path() -> Path:
    local = script_dir() / "jbrowse.state"
    if local.exists():
        return local

    return Path.home() / ".cache" / APP_NAME / "jbrowse.state"


@dataclasses.dataclass(frozen=True)
class Config:
    path: Path
    jellyfin_url: str
    username: str
    password: str
    item_types: list[str]
    initial_view: str
    max_display_items: int


@dataclasses.dataclass(frozen=True)
class State:
    path: Path
    deviceid: str


@dataclasses.dataclass(frozen=True)
class Auth:
    user_id: str
    token: str


@dataclasses.dataclass(frozen=True)
class MediaItem:
    id: str
    title: str
    kind: str
    date_created: str
    last_played: str
    resume_ticks: int

    @property
    def resume_seconds(self) -> float:
        return self.resume_ticks / TICKS_PER_SECOND


class JellyfinError(RuntimeError):
    pass


def missing_cfg_message(path: Path) -> str:
    return (
        f"No config found. Create {path} with something like:\n\n"
        "[jellyfin]\n"
        "url = http://127.0.0.1:8096\n"
        "username = bryan\n"
        "password = your-password\n\n"
        "[library]\n"
        "types = Movie,Episode,Video,MusicVideo\n\n"
        "[ui]\n"
        "initial_view = played\n"
        "max_display_items = 300\n"
    )


def load_cfg(path: Path) -> Config:
    if not path.exists():
        die(missing_cfg_message(path))

    parser = configparser.ConfigParser()
    parser.read(path)

    try:
        jellyfin_url = parser["jellyfin"]["url"].rstrip("/")
        username = parser["jellyfin"]["username"]
        password = parser["jellyfin"]["password"]
    except KeyError as exc:
        die(f"Missing config key in {path}: {exc}")

    if not jellyfin_url:
        die(f"Missing Jellyfin URL in {path}")
    if not username:
        die(f"Missing Jellyfin username in {path}")
    if not password:
        die(f"Missing Jellyfin password in {path}")

    types_raw = parser.get("library", "types", fallback="Movie,Episode,Video,MusicVideo")
    item_types = [x.strip() for x in types_raw.split(",") if x.strip()]
    if not item_types:
        die(f"No item types configured in {path}")

    initial_view = parser.get("ui", "initial_view", fallback="played").strip().lower()
    if initial_view not in {"played", "added"}:
        die("ui.initial_view must be played or added")

    return Config(
        path=path,
        jellyfin_url=jellyfin_url,
        username=username,
        password=password,
        item_types=item_types,
        initial_view=initial_view,
        max_display_items=max(
            1,
            parser.getint("ui", "max_display_items", fallback=DEFAULT_VISIBLE_ITEMS),
        ),
    )


def load_state(path: Path) -> State:
    parser = configparser.ConfigParser()

    if path.exists():
        parser.read(path)

    if not parser.has_section("state"):
        parser.add_section("state")

    deviceid = parser.get("state", "deviceid", fallback="").strip()

    if not deviceid:
        deviceid = secrets.token_hex(16)
        parser.set("state", "deviceid", deviceid)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as fh:
            parser.write(fh)

    return State(path=path, deviceid=deviceid)


class JellyfinClient:
    def __init__(self, cfg: Config, state: State):
        self.cfg = cfg
        self.state = state
        self.session = requests.Session()
        self.auth: Optional[Auth] = None

    def auth_header(self, token: Optional[str] = None) -> str:
        parts = {
            "MediaBrowser Client": CLIENT_NAME,
            "Device": socket.gethostname(),
            "DeviceId": self.state.deviceid,
            "Version": CLIENT_VERSION,
        }

        if token:
            parts["Token"] = token

        return ", ".join(f'{key}="{value}"' for key, value in parts.items())

    def headers(self) -> dict[str, str]:
        token = self.auth.token if self.auth else None
        headers = {"X-Emby-Authorization": self.auth_header(token)}

        if token:
            headers["X-MediaBrowser-Token"] = token

        return headers

    def login(self) -> None:
        try:
            response = self.session.post(
                f"{self.cfg.jellyfin_url}/Users/AuthenticateByName",
                headers={
                    "X-Emby-Authorization": self.auth_header(),
                    "Content-Type": "application/json",
                },
                json={"Username": self.cfg.username, "Pw": self.cfg.password},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise JellyfinError(f"login failed: {exc}") from exc

        data = response.json()

        try:
            self.auth = Auth(
                user_id=data["User"]["Id"],
                token=data["AccessToken"],
            )
        except KeyError as exc:
            raise JellyfinError(f"unexpected login response; missing {exc}") from exc

    def fetch_items(self) -> list[MediaItem]:
        if self.auth is None:
            self.login()

        assert self.auth is not None

        items: list[MediaItem] = []
        start = 0
        limit = 250

        while True:
            params = {
                "Recursive": "true",
                "IncludeItemTypes": ",".join(self.cfg.item_types),
                "Fields": "DateCreated,UserData,SeriesName,ParentIndexNumber,IndexNumber,ProductionYear",
                "StartIndex": str(start),
                "Limit": str(limit),
                "SortBy": "DateCreated",
                "SortOrder": "Descending",
            }

            try:
                response = self.session.get(
                    f"{self.cfg.jellyfin_url}/Users/{self.auth.user_id}/Items",
                    headers=self.headers(),
                    params=params,
                    timeout=60,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                raise JellyfinError(f"item fetch failed: {exc}") from exc

            data = response.json()
            raw_items = data.get("Items", [])
            total = int(data.get("TotalRecordCount", len(items) + len(raw_items)))

            for raw in raw_items:
                item = parse_item(raw)
                if item:
                    items.append(item)

            start += len(raw_items)

            if not raw_items or start >= total:
                return items

    def stream_url(self, item: MediaItem) -> str:
        if self.auth is None:
            raise JellyfinError("not logged in")

        endpoint = f"/Videos/{item.id}/stream"
        if item.kind.lower() == "audio":
            endpoint = f"/Audio/{item.id}/stream"

        return (
            f"{self.cfg.jellyfin_url}{endpoint}"
            f"?static=true"
            f"&api_key={self.auth.token}"
            f"&DeviceId={self.state.deviceid}"
        )


def parse_item(raw: dict[str, Any]) -> Optional[MediaItem]:
    item_id = raw.get("Id")
    name = raw.get("Name") or ""
    kind = raw.get("Type") or ""

    if not item_id or not name or not kind:
        return None

    user_data = raw.get("UserData") or {}

    return MediaItem(
        id=item_id,
        title=make_title(raw),
        kind=kind,
        date_created=raw.get("DateCreated") or "",
        last_played=user_data.get("LastPlayedDate") or "",
        resume_ticks=int(user_data.get("PlaybackPositionTicks") or 0),
    )


def make_title(raw: dict[str, Any]) -> str:
    # Episodes need context in one big flat list. Movies usually do not.
    name = raw.get("Name") or ""
    kind = raw.get("Type") or ""

    if kind == "Episode":
        series = raw.get("SeriesName") or ""
        season = raw.get("ParentIndexNumber")
        episode = raw.get("IndexNumber")

        if series and season is not None and episode is not None:
            return f"{series} - S{int(season):02d}E{int(episode):02d} - {name}"

        if series:
            return f"{series} - {name}"

    year = raw.get("ProductionYear")
    if kind == "Movie" and year:
        return f"{name} ({year})"

    return name


def parse_jf_date(value: str) -> dt.datetime:
    if not value:
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)

    return parsed


def sorted_views(items: list[MediaItem]) -> dict[str, list[MediaItem]]:
    played = [item for item in items if item.last_played]

    return {
        "played": sorted(
            played,
            key=lambda item: parse_jf_date(item.last_played),
            reverse=True,
        ),
        "added": sorted(
            items,
            key=lambda item: parse_jf_date(item.date_created),
            reverse=True,
        ),
    }


class BrowseApp(App[Optional[MediaItem]]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #query {
        height: 3;
        border: solid $accent;
    }

    #status {
        height: 1;
    }

    #items {
        height: 1fr;
    }
    """

    def __init__(self, cfg: Config, items: list[MediaItem]):
        super().__init__()
        self.cfg = cfg
        self.views = sorted_views(items)
        self.view = cfg.initial_view
        self.all_count = len(items)
        self.filtered_items: list[MediaItem] = []
        self.visible_items: list[MediaItem] = []
        self.regex_error = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(id="query")
            yield Label("", id="status")
            yield ListView(id="items")

    @property
    def query(self) -> Input:
        return self.query_one("#query", Input)

    @property
    def listbox(self) -> ListView:
        return self.query_one("#items", ListView)

    @property
    def status(self) -> Label:
        return self.query_one("#status", Label)

    def on_mount(self) -> None:
        self.query.focus()
        self.apply_filter()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.apply_filter()

    def on_key(self, event) -> None:
        # Do this manually because Tab can be swallowed by focus handling.
        if event.key == "tab":
            self.toggle_view()
            event.stop()
            return

        if self.focused is self.query and event.key == "down":
            if self.visible_items:
                self.listbox.focus()
                self.listbox.index = 0
                event.stop()
            return

        if self.focused is self.listbox:
            if event.key in {"left", "right"}:
                self.toggle_view()
                event.stop()
                return

            if event.key == "up" and self.listbox.index == 0:
                self.query.focus()
                event.stop()
                return

            if event.key == "backspace":
                self.query.value = self.query.value[:-1]
                self.query.cursor_position = len(self.query.value)
                self.query.focus()
                event.stop()
                return

            typed = getattr(event, "character", None)
            if typed is None and len(event.key) == 1:
                typed = event.key

            if typed and typed.isprintable():
                self.query.value += typed
                self.query.cursor_position = len(self.query.value)
                self.query.focus()
                event.stop()
                return

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = self.listbox.index

        if index is None:
            return

        try:
            self.exit(self.visible_items[index])
        except IndexError:
            return

    def action_clear_search(self) -> None:
        self.query.value = ""
        self.query.focus()

    def toggle_view(self) -> None:
        self.view = "added" if self.view == "played" else "played"
        self.apply_filter()

    def apply_filter(self) -> None:
        text = self.query.value.strip()
        self.regex_error = ""

        source = self.views[self.view]

        if not text:
            matched = source
        elif text.startswith("/"):
            pattern = text[1:]

            if not pattern:
                matched = source
            else:
                try:
                    regex = re.compile(pattern, re.IGNORECASE)
                except re.error as exc:
                    self.regex_error = str(exc)
                    matched = []
                else:
                    matched = [item for item in source if regex.search(item.title)]
        else:
            needle = text.casefold()
            matched = [item for item in source if needle in item.title.casefold()]

        self.filtered_items = matched
        self.visible_items = matched[: self.cfg.max_display_items]

        self.rebuild_list()
        self.update_status()

    def rebuild_list(self) -> None:
        self.listbox.clear()

        for item in self.visible_items:
            self.listbox.append(ListItem(Label(item.title)))

        if self.visible_items:
            self.listbox.index = 0

    def update_status(self) -> None:
        parts = [
            self.view,
            f"{self.all_count} loaded",
            f"{len(self.filtered_items)} matched",
            f"showing {len(self.visible_items)}",
        ]

        if self.regex_error:
            parts.append(f"regex error: {self.regex_error}")

        parts.append("tab/←/→ switch")
        parts.append("enter play")
        parts.append("ctrl+c quit")

        self.status.update(" | ".join(parts))


def play_item(client: JellyfinClient, item: MediaItem) -> int:
    url = client.stream_url(item)

    args = [
        "mpv",
        "--hwdec=auto",
        f"--force-media-title={item.title}",
    ]

    if item.resume_seconds > 0:
        args.append(f"--start={item.resume_seconds:.3f}")

    args.append(url)

    print(f"Now Playing: \033[1;32m{item.title}\033[0m")

    try:
        return subprocess.run(args).returncode
    except FileNotFoundError:
        die("Could not find mpv executable: mpv")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny Jellyfin TUI launcher for mpv")
    parser.add_argument("--config", help="override config path")
    parser.add_argument("--state", help="override state path")
    parser.add_argument("--print-config-path", action="store_true")
    parser.add_argument("--print-state-path", action="store_true")
    return parser.parse_args()


def browser_loop(cfg: Config, client: JellyfinClient, items: list[MediaItem]) -> int:
    while True:
        chosen = BrowseApp(cfg, items).run()

        if chosen is None:
            return 0

        play_item(client, chosen)

        print("Refreshing Jellyfin state...", file=sys.stderr)

        try:
            items = client.fetch_items()
        except JellyfinError as exc:
            print(f"Jellyfin refresh failed: {exc}", file=sys.stderr)
            print("Returning with old item list.", file=sys.stderr)


def main() -> int:
    args = parse_args()

    cfg_path = Path(args.config).expanduser() if args.config else default_cfg_path()
    state_path = Path(args.state).expanduser() if args.state else default_state_path()

    if args.print_config_path:
        print(cfg_path)
        return 0

    if args.print_state_path:
        print(state_path)
        return 0

    cfg = load_cfg(cfg_path)
    state = load_state(state_path)
    client = JellyfinClient(cfg, state)

    print(f"Using config: {cfg.path}", file=sys.stderr)
    print(f"Using state: {state.path}", file=sys.stderr)
    print("Logging into Jellyfin...", file=sys.stderr)

    try:
        client.login()
        items = client.fetch_items()
    except JellyfinError as exc:
        die(f"Jellyfin error: {exc}")

    if not items:
        die("No playable Jellyfin items found.")

    return browser_loop(cfg, client, items)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
