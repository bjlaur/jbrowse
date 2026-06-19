#!/usr/bin/env python3
"""
jbrowse - tiny Jellyfin TUI launcher for mpv

Config:
  1. jbrowse.conf next to this script
  2. ~/.config/jbrowse/jbrowse.conf

State:
  1. jbrowse.state next to this script, if it exists
  2. ~/.cache/jbrowse/jbrowse.state

Style:
  1. --style path, if provided
  2. [style] path in jbrowse.conf, if provided
  3. jbrowse.tcss next to this script, if it exists
  4. ~/.config/jbrowse/jbrowse.tcss, if it exists
  5. built-in fallback

Secret theme preview:
  Ctrl+X cycles discovered .tcss files from themes/ and config dirs.

Playback:
  mpv --hwdec=auto --force-media-title="$filename" $subtitle $start "$url"

Dependencies:
  pip install textual requests
"""

from __future__ import annotations

import argparse
import configparser
import json
import dataclasses
import datetime as dt
import os
import queue
import re
import secrets
import shlex
import socket
import string
import subprocess
import sys
import threading
import time
import textwrap
import urllib.parse
from pathlib import Path
from typing import Any, Optional
from rich.text import Text
from rich.align import Align
from rich.panel import Panel

try:
    import requests
except ImportError:
    print("Missing dependency: requests\nInstall with: pip install requests", file=sys.stderr)
    raise SystemExit(1)

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Input, Label, Static
except ImportError:
    print("Missing dependency: textual\nInstall with: pip install textual", file=sys.stderr)
    raise SystemExit(1)


APP_NAME = "jbrowse"
CLIENT_NAME = "jbrowse"
CLIENT_VERSION = "0.0.32"
TICKS_PER_SECOND = 10_000_000
DEFAULT_VISIBLE_ITEMS = 300
CACHE_VERSION = 2
DEFAULT_MPV_CMD_TEMPLATE = 'mpv --hwdec=auto --force-media-title="$filename" $subtitle $start "$url"'
DEFAULT_REFRESH_INTERVAL_MINUTES = 10
REFRESH_ACTIVE_WINDOW_SECONDS = 10 * 60
REFRESH_CHECK_SECONDS = 30
SORT_MODE_ORDER = ["added", "played", "premiere", "name", "series"]
SORT_MODE_LABELS = {
    "added": "recently added",
    "played": "last played",
    "premiere": "premiere date",
    "name": "name",
    "series": "series order",
}


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


def default_item_cache_path() -> Path:
    local = script_dir() / "jbrowse.items.json"
    if local.exists():
        return local

    return Path.home() / ".cache" / APP_NAME / "jbrowse.items.json"


def default_style_path() -> Optional[Path]:
    local = script_dir() / "jbrowse.tcss"
    if local.exists():
        return local

    fallback = Path.home() / ".config" / APP_NAME / "jbrowse.tcss"
    if fallback.exists():
        return fallback

    return None


def expand_style_path(value: str, cfg_path: Path) -> Optional[Path]:
    value = value.strip()
    if not value:
        return None

    path = Path(value).expanduser()

    if not path.is_absolute():
        direct = cfg_path.parent / path
        themed = cfg_path.parent / "themes" / path

        # Keep old configs working after committed themes moved under themes/.
        if not direct.exists() and themed.exists():
            return themed

        path = direct

    return path



def style_path_for_config(theme_path: Path, cfg_path: Path) -> str:
    """Prefer a relative path when the theme sits under the config directory."""
    try:
        return str(theme_path.relative_to(cfg_path.parent))
    except ValueError:
        return str(theme_path)


def persist_style_path(cfg: Config, theme: Theme) -> None:
    """Save the currently selected theme under [style] path in jbrowse.conf."""
    if theme.path is None:
        return

    parser = configparser.ConfigParser(strict=False)

    if cfg.path.exists():
        parser.read(cfg.path)

    if not parser.has_section("style"):
        parser.add_section("style")

    parser.set("style", "path", style_path_for_config(theme.path, cfg.path))

    try:
        with cfg.path.open("w", encoding="utf-8") as fh:
            parser.write(fh)
    except OSError as exc:
        print(f"Could not persist style to {cfg.path}: {exc}", file=sys.stderr)



def persist_ui_values(cfg: Config, values: dict[str, str]) -> None:
    """Save small UI preferences under [ui] in jbrowse.conf."""
    parser = configparser.ConfigParser(strict=False)

    if cfg.path.exists():
        parser.read(cfg.path)

    if not parser.has_section("ui"):
        parser.add_section("ui")

    for key, value in values.items():
        parser.set("ui", key, value)

    try:
        with cfg.path.open("w", encoding="utf-8") as fh:
            parser.write(fh)
    except OSError as exc:
        print(f"Could not persist UI settings to {cfg.path}: {exc}", file=sys.stderr)


def persist_display_mode(cfg: Config, display_mode: str) -> None:
    """Save the current title/filename display mode under [ui]."""
    persist_ui_values(cfg, {"display_mode": display_mode})


def persist_sort_state(cfg: Config, sort_mode: str, sort_desc: bool) -> None:
    """Save current sort mode and direction under [ui]."""
    persist_ui_values(
        cfg,
        {
            "sort_mode": sort_mode,
            "sort_desc": "true" if sort_desc else "false",
        },
    )


@dataclasses.dataclass(frozen=True)
class Theme:
    name: str
    path: Optional[Path]
    tcss: str


class ThemeCycle:
    pass


@dataclasses.dataclass(frozen=True)
class PlaybackRequest:
    item: "MediaItem"
    subtitle_choice: str = "auto"


@dataclasses.dataclass(frozen=True)
class PlaybackResult:
    return_code: int
    command: str
    output: str


@dataclasses.dataclass
class UIState:
    view: str = ""
    display_mode: str = ""
    sort_desc: bool = True
    query: str = ""
    selected_item_id: str = ""
    scroll_offset: int = 0
    focus: str = "query"
    page: str = "browser"
    previous_page: str = "browser"
    info_item_id: str = ""
    info_scroll: int = 0
    mpv_log_scroll: int = 0
    subtitle_choices: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class SubtitleTrack:
    key: str
    title: str
    mpv_sid: str
    language: str = ""
    default: bool = False
    forced: bool = False
    external: bool = False


DEFAULT_TCSS = """
Screen {
    layout: vertical;
    background: #111318;
    color: #d8dee9;
}

#top_status {
    height: 1;
    background: #222631;
    color: #d8dee9;
    padding: 0 1;
}

#query {
    height: 1;
    border: none;
    padding: 0 1;
    margin: 0;
    background: #1f3a4d;
    color: #ffffff;
}

#query:focus {
    background: #284d66;
}

#items {
    height: 1fr;
    background: #111318;
    padding: 0 1;
}

#bottom_status {
    height: 1;
    background: #111318;
    color: #6d7480;
    padding: 0 1;
}

"""


def read_tcss(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        die(f"Could not read style file {path}: {exc}")


def initial_theme(style_path: Optional[Path]) -> Theme:
    if style_path is not None:
        return Theme(name=style_path.name, path=style_path, tcss=read_tcss(style_path))

    fallback = default_style_path()
    if fallback is not None:
        return Theme(name=fallback.name, path=fallback, tcss=read_tcss(fallback))

    return Theme(name="built-in", path=None, tcss=DEFAULT_TCSS)


def discover_themes(start: Theme) -> list[Theme]:
    themes: list[Theme] = []
    seen_names: set[str] = set()

    def add_path(path: Path) -> None:
        name = path.name
        if name in seen_names:
            return
        if not path.exists() or not path.is_file():
            return
        seen_names.add(name)
        themes.append(Theme(name=name, path=path, tcss=read_tcss(path)))

    # The active explicit/configured file gets first claim on its filename.
    if start.path is not None:
        add_path(start.path)
        search_dirs = [
            start.path.parent,
            script_dir() / "themes",
            script_dir(),
            Path.home() / ".config" / APP_NAME / "themes",
            Path.home() / ".config" / APP_NAME,
        ]
    else:
        search_dirs = [
            script_dir() / "themes",
            script_dir(),
            Path.home() / ".config" / APP_NAME / "themes",
            Path.home() / ".config" / APP_NAME,
        ]

    for directory in search_dirs:
        if not directory.exists() or not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.tcss")):
            add_path(path)

    if not themes:
        themes.append(start)

    return themes


@dataclasses.dataclass(frozen=True)
class Config:
    path: Path
    jellyfin_url: str
    username: str
    password: str
    item_types: list[str]
    initial_view: str
    sort_mode: str
    sort_desc: bool
    max_display_items: int
    display_mode: str
    style_path: Optional[Path]
    mpv_cmd: list[str]
    refresh_interval_minutes: int


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
    filename: str
    kind: str
    series_name: str
    season_number: Optional[int]
    episode_number: Optional[int]
    premiere_date: str
    date_created: str
    last_played: str
    resume_ticks: int
    info_lines: list[str]
    subtitle_tracks: list[SubtitleTrack]

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
        "username = your-login\n"
        "password = your-password\n\n"
        "[library]\n"
        "types = Movie,Episode,Video,MusicVideo\n\n"
        "[ui]\n"
        "# sort_mode can be: added, played, premiere, name, series\n"
        "sort_mode = added\n"
        "sort_desc = true\n"
        "max_display_items = 300\n"
        "# title or filename\n"
        "display_mode = title\n\n"
        "[style]\n"
        "# Optional. Relative paths are relative to jbrowse.conf.\n"
        "# path = themes/03-jbrowse-batman-low-contrast.tcss\n"
        "\n[cache]\n"
        "# 0 disables periodic refresh.\n"
        "refresh_interval_minutes = 10\n"
    )


def is_placeholder_token(token: str, name: str) -> bool:
    return token in {f"${name}", f"${{{name}}}", f"{{{name}}}"}


def token_has_placeholder(token: str, name: str) -> bool:
    return any(placeholder in token for placeholder in (f"${name}", f"${{{name}}}", f"{{{name}}}"))


def load_mpv_cmd(parser: configparser.ConfigParser, path: Path) -> list[str]:
    raw = parser.get("mpv", "mpv_cmd", fallback=DEFAULT_MPV_CMD_TEMPLATE).strip()

    if not raw:
        die(f"Empty mpv.mpv_cmd in {path}")

    try:
        command = shlex.split(raw)
    except ValueError as exc:
        die(f"Could not parse mpv.mpv_cmd in {path}: {exc}")

    if not command:
        die(f"Empty mpv.mpv_cmd in {path}")
    if not any(token_has_placeholder(token, "url") for token in command):
        die("mpv.mpv_cmd must include $url or {url}")

    return command


def load_cfg(path: Path) -> Config:
    if not path.exists():
        die(missing_cfg_message(path))

    # strict=False means a duplicate key while editing keeps the later value.
    parser = configparser.ConfigParser(strict=False)
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

    legacy_initial_view = parser.get("ui", "initial_view", fallback="added").strip().lower()
    sort_mode = parser.get("ui", "sort_mode", fallback=legacy_initial_view).strip().lower()
    if sort_mode not in SORT_MODE_ORDER:
        die("ui.sort_mode must be one of: " + ", ".join(SORT_MODE_ORDER))

    sort_desc = parser.getboolean("ui", "sort_desc", fallback=True)

    display_mode = parser.get("ui", "display_mode", fallback="title").strip().lower()
    if display_mode not in {"title", "filename"}:
        die("ui.display_mode must be title or filename")

    style_value = parser.get("style", "path", fallback="")
    style_path = expand_style_path(style_value, path)
    mpv_cmd = load_mpv_cmd(parser, path)
    refresh_interval_minutes = parser.getint(
        "cache",
        "refresh_interval_minutes",
        fallback=DEFAULT_REFRESH_INTERVAL_MINUTES,
    )
    if refresh_interval_minutes < 0:
        die("cache.refresh_interval_minutes must be 0 or greater")

    return Config(
        path=path,
        jellyfin_url=jellyfin_url,
        username=username,
        password=password,
        item_types=item_types,
        initial_view=sort_mode,
        sort_mode=sort_mode,
        sort_desc=sort_desc,
        max_display_items=max(
            0,
            parser.getint("ui", "max_display_items", fallback=DEFAULT_VISIBLE_ITEMS),
        ),
        display_mode=display_mode,
        style_path=style_path,
        mpv_cmd=mpv_cmd,
        refresh_interval_minutes=refresh_interval_minutes,
    )


def load_state(path: Path) -> State:
    parser = configparser.ConfigParser(strict=False)

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
                "Fields": "DateCreated,UserData,SeriesName,ParentIndexNumber,IndexNumber,ProductionYear,Path,MediaSources,Overview,Genres,OfficialRating,CommunityRating,PremiereDate,RunTimeTicks,ProviderIds,SortName",
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

    def post_playback_report(self, endpoint: str, payload: dict[str, Any]) -> None:
        if self.auth is None:
            raise JellyfinError("not logged in")

        try:
            response = self.session.post(
                f"{self.cfg.jellyfin_url}{endpoint}",
                headers={**self.headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise JellyfinError(f"playback report failed: {exc}") from exc

    def report_playback_started(self, payload: dict[str, Any]) -> None:
        self.post_playback_report("/Sessions/Playing", payload)

    def report_playback_progress(self, payload: dict[str, Any]) -> None:
        self.post_playback_report("/Sessions/Playing/Progress", payload)

    def report_playback_stopped(self, payload: dict[str, Any]) -> None:
        self.post_playback_report("/Sessions/Playing/Stopped", payload)


class FakeJellyfinClient:
    """Local fixture client used by --fake; it never contacts Jellyfin."""

    def __init__(self, cfg: Config, items: list[MediaItem]):
        self.cfg = cfg
        self.auth = Auth(user_id="fixture-user", token="fixture-token")
        self.items = items

    def fetch_items(self) -> list[MediaItem]:
        return list(self.items)

    def stream_url(self, item: MediaItem) -> str:
        return "file:///dev/null"

    def report_playback_started(self, payload: dict[str, Any]) -> None:
        pass

    def report_playback_progress(self, payload: dict[str, Any]) -> None:
        pass

    def report_playback_stopped(self, payload: dict[str, Any]) -> None:
        pass


def optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_item(raw: dict[str, Any]) -> Optional[MediaItem]:
    item_id = raw.get("Id")
    name = raw.get("Name") or ""
    kind = raw.get("Type") or ""

    if not item_id or not name or not kind:
        return None

    user_data = raw.get("UserData") or {}

    title = make_title(raw)
    filename = make_filename(raw) or title

    return MediaItem(
        id=item_id,
        title=title,
        filename=filename,
        kind=kind,
        series_name=raw.get("SeriesName") or "",
        season_number=optional_int(raw.get("ParentIndexNumber")),
        episode_number=optional_int(raw.get("IndexNumber")),
        premiere_date=raw.get("PremiereDate") or "",
        date_created=raw.get("DateCreated") or "",
        last_played=user_data.get("LastPlayedDate") or "",
        resume_ticks=int(user_data.get("PlaybackPositionTicks") or 0),
        info_lines=make_info_lines(raw, title, filename),
        subtitle_tracks=subtitle_tracks(raw),
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



def make_filename(raw: dict[str, Any]) -> str:
    """Best-effort filename from Jellyfin metadata."""
    path = raw.get("Path") or ""

    if not path:
        for source in raw.get("MediaSources") or []:
            path = source.get("Path") or source.get("Name") or ""
            if path:
                break

    if not path:
        return ""

    return os.path.basename(path.rstrip("/")) or path



def format_seconds(seconds: float) -> str:
    seconds = int(max(0, seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def format_runtime_minutes(ticks: int) -> str:
    if not ticks:
        return ""

    minutes = round((ticks / TICKS_PER_SECOND) / 60)

    if minutes <= 0:
        return ""

    return f"{minutes} m"


def format_date_short(value: str) -> str:
    if not value:
        return ""

    parsed = parse_jf_date(value)
    if parsed == dt.datetime.min.replace(tzinfo=dt.timezone.utc):
        return value

    return f"{parsed.month}/{parsed.day}/{parsed.year}"


def first_media_path(raw: dict[str, Any]) -> str:
    path = raw.get("Path") or ""

    if path:
        return path

    for source in raw.get("MediaSources") or []:
        path = source.get("Path") or ""
        if path:
            return path

    return ""


def first_media_source(raw: dict[str, Any]) -> dict[str, Any]:
    sources = raw.get("MediaSources") or []

    if sources and isinstance(sources[0], dict):
        return sources[0]

    return {}


def media_streams(raw: dict[str, Any]) -> list[dict[str, Any]]:
    source = first_media_source(raw)
    streams = source.get("MediaStreams") or raw.get("MediaStreams") or []

    return [stream for stream in streams if isinstance(stream, dict)]


def stream_display_title(stream: dict[str, Any]) -> str:
    return (
        stream.get("DisplayTitle")
        or stream.get("Title")
        or stream.get("Codec")
        or stream.get("Type")
        or ""
    )


def first_stream_title(raw: dict[str, Any], stream_type: str) -> str:
    for stream in media_streams(raw):
        if (stream.get("Type") or "").lower() == stream_type.lower():
            return stream_display_title(stream)

    return ""


def best_subtitle_title(raw: dict[str, Any]) -> str:
    for stream in media_streams(raw):
        if (stream.get("Type") or "").lower() == "subtitle" and stream.get("IsDefault"):
            return stream_display_title(stream)

    for stream in media_streams(raw):
        if (stream.get("Type") or "").lower() == "subtitle":
            return stream_display_title(stream)

    return ""


def subtitle_track_title(stream: dict[str, Any], ordinal: int) -> str:
    title = stream_display_title(stream) or f"Subtitle {ordinal}"
    details = []

    if stream.get("IsDefault"):
        details.append("default")
    if stream.get("IsForced"):
        details.append("forced")
    if stream.get("IsExternal"):
        details.append("external")

    if details:
        return f"{title} ({', '.join(details)})"

    return title


def subtitle_tracks(raw: dict[str, Any]) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []

    for ordinal, stream in enumerate(
        [s for s in media_streams(raw) if (s.get("Type") or "").lower() == "subtitle"],
        start=1,
    ):
        stream_index = stream.get("Index")
        key_index = stream_index if stream_index is not None else ordinal

        tracks.append(
            SubtitleTrack(
                key=f"stream:{key_index}",
                title=subtitle_track_title(stream, ordinal),
                mpv_sid=str(ordinal),
                language=str(stream.get("Language") or ""),
                default=bool(stream.get("IsDefault")),
                forced=bool(stream.get("IsForced")),
                external=bool(stream.get("IsExternal")),
            )
        )

    return tracks


def add_kv(lines: list[str], label: str, value: Any) -> None:
    if value is None or value == "":
        return

    if isinstance(value, bool):
        value = "yes" if value else "No"

    lines.append(f"{label:<14} {value}")


def add_section(lines: list[str], title: str) -> None:
    if lines and lines[-1] != "":
        lines.append("")
    lines.append(title)
    lines.append("-" * len(title))


def stream_lines(stream: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    add_kv(lines, "Title", stream_display_title(stream))
    add_kv(lines, "Language", stream.get("Language"))
    add_kv(lines, "Codec", stream.get("Codec"))
    add_kv(lines, "Profile", stream.get("Profile"))
    add_kv(lines, "Level", stream.get("Level"))

    width = stream.get("Width")
    height = stream.get("Height")
    if width and height:
        add_kv(lines, "Resolution", f"{width}x{height}")

    aspect = stream.get("AspectRatio") or stream.get("DisplayAspectRatio")
    add_kv(lines, "Aspect ratio", aspect)
    add_kv(lines, "Anamorphic", stream.get("IsAnamorphic"))
    add_kv(lines, "Interlaced", stream.get("IsInterlaced"))

    framerate = stream.get("RealFrameRate") or stream.get("AverageFrameRate")
    add_kv(lines, "Framerate", framerate)

    bitrate = stream.get("BitRate")
    if bitrate:
        add_kv(lines, "Bitrate", f"{round(int(bitrate) / 1000)} kbps")

    add_kv(lines, "Bit depth", stream.get("BitDepth"))
    add_kv(lines, "Video range", stream.get("VideoRange"))
    add_kv(lines, "Video range type", stream.get("VideoRangeType"))
    add_kv(lines, "Color space", stream.get("ColorSpace"))
    add_kv(lines, "Color transfer", stream.get("ColorTransfer"))
    add_kv(lines, "Color primaries", stream.get("ColorPrimaries"))
    add_kv(lines, "Pixel format", stream.get("PixelFormat"))
    add_kv(lines, "Ref frames", stream.get("RefFrames"))

    layout = stream.get("ChannelLayout")
    channels = stream.get("Channels")
    add_kv(lines, "Layout", layout)
    if channels:
        add_kv(lines, "Channels", f"{channels} ch")

    sample_rate = stream.get("SampleRate")
    if sample_rate:
        add_kv(lines, "Sample rate", f"{sample_rate} Hz")

    add_kv(lines, "Default", stream.get("IsDefault"))
    add_kv(lines, "Forced", stream.get("IsForced"))
    add_kv(lines, "External", stream.get("IsExternal"))

    return lines


def technical_detail_lines(raw: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    source = first_media_source(raw)

    add_section(lines, "Technical Details")
    add_kv(lines, "Container", source.get("Container") or raw.get("Container"))
    add_kv(lines, "Path", first_media_path(raw))

    size = source.get("Size") or raw.get("Size")
    if size:
        gib = int(size) / (1024 ** 3)
        add_kv(lines, "Size", f"{gib:.1f} GiB")

    streams = media_streams(raw)

    for stream_type in ["Video", "Audio", "Subtitle"]:
        matching = [s for s in streams if (s.get("Type") or "").lower() == stream_type.lower()]
        for index, stream in enumerate(matching, start=1):
            heading = stream_type if len(matching) == 1 else f"{stream_type} {index}"
            add_section(lines, heading)
            lines.extend(stream_lines(stream))

    return lines


def make_info_lines(raw: dict[str, Any], title: str, filename: str) -> list[str]:
    user_data = raw.get("UserData") or {}
    lines: list[str] = []

    series = raw.get("SeriesName") or raw.get("Name") or title
    episode_name = raw.get("Name") or ""
    season = raw.get("ParentIndexNumber")
    episode = raw.get("IndexNumber")
    kind = raw.get("Type") or ""

    if kind == "Episode" and series:
        lines.append(series.upper())
        if season is not None and episode is not None:
            lines.append(f"Season {season} - {episode}. {episode_name}")
        else:
            lines.append(episode_name)
    else:
        lines.append(title)

    meta_parts = []
    date = format_date_short(raw.get("PremiereDate") or raw.get("DateCreated") or "")
    runtime = format_runtime_minutes(int(raw.get("RunTimeTicks") or 0))
    community_rating = raw.get("CommunityRating")

    if date:
        meta_parts.append(date)
    if runtime:
        meta_parts.append(runtime)
    if community_rating:
        meta_parts.append(f"★ {community_rating}")

    if meta_parts:
        lines.append("   ".join(meta_parts))

    lines.append("")

    video = first_stream_title(raw, "Video")
    audio = first_stream_title(raw, "Audio")
    subtitle = best_subtitle_title(raw)

    if video:
        add_kv(lines, "Video", video)
    if audio:
        add_kv(lines, "Audio", audio)
    if subtitle:
        add_kv(lines, "Subtitles", subtitle)

    overview = (raw.get("Overview") or "").strip()
    if overview:
        lines.append("")
        for wrapped in textwrap.wrap(overview, width=88):
            lines.append(wrapped)

    provider_ids = raw.get("ProviderIds") or {}
    links = []
    if provider_ids.get("Imdb"):
        links.append("IMDb")
    if provider_ids.get("Tmdb"):
        links.append("TMDB")
    if links:
        lines.append("")
        lines.append(", ".join(links))

    genres = raw.get("Genres") or []
    if genres:
        lines.append("")
        add_kv(lines, "Genres", ", ".join(genres))

    lines.append("")
    lines.extend(technical_detail_lines(raw))

    return lines

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


def title_sort_key(item: MediaItem) -> str:
    return item.title.casefold()


def series_sort_key(item: MediaItem) -> tuple[str, int, int, dt.datetime, str]:
    if item.kind == "Episode":
        series = item.series_name.casefold() or item.title.casefold()
        season = item.season_number if item.season_number is not None else 9999
        episode = item.episode_number if item.episode_number is not None else 9999
        date = parse_jf_date(item.premiere_date or item.date_created)
        return (series, season, episode, date, item.title.casefold())

    return (item.title.casefold(), 9999, 9999, parse_jf_date(item.premiere_date or item.date_created), item.title.casefold())


def sorted_views(items: list[MediaItem]) -> dict[str, list[MediaItem]]:
    return {
        "played": sorted(
            items,
            key=lambda item: (
                1 if item.last_played else 0,
                parse_jf_date(item.last_played),
                parse_jf_date(item.date_created),
            ),
            reverse=True,
        ),
        "added": sorted(
            items,
            key=lambda item: parse_jf_date(item.date_created),
            reverse=True,
        ),
        "premiere": sorted(
            items,
            key=lambda item: parse_jf_date(item.premiere_date or item.date_created),
            reverse=True,
        ),
        "name": sorted(
            items,
            key=title_sort_key,
        ),
        "series": sorted(
            items,
            key=series_sort_key,
        ),
    }



def find_item_by_id(items: list[MediaItem], item_id: str) -> Optional[MediaItem]:
    if not item_id:
        return None

    for item in items:
        if item.id == item_id:
            return item

    return None



def media_item_to_cache(item: MediaItem) -> dict[str, Any]:
    return dataclasses.asdict(item)


def subtitle_track_from_cache(row: dict[str, Any]) -> Optional[SubtitleTrack]:
    try:
        return SubtitleTrack(
            key=str(row["key"]),
            title=str(row["title"]),
            mpv_sid=str(row["mpv_sid"]),
            language=str(row.get("language") or ""),
            default=bool(row.get("default")),
            forced=bool(row.get("forced")),
            external=bool(row.get("external")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def media_item_from_cache(row: dict[str, Any]) -> Optional[MediaItem]:
    try:
        cached_subtitles = []
        for subtitle_row in row.get("subtitle_tracks", []):
            if not isinstance(subtitle_row, dict):
                continue
            track = subtitle_track_from_cache(subtitle_row)
            if track is not None:
                cached_subtitles.append(track)

        return MediaItem(
            id=str(row["id"]),
            title=str(row["title"]),
            filename=str(row.get("filename") or row["title"]),
            kind=str(row.get("kind") or ""),
            series_name=str(row.get("series_name") or ""),
            season_number=optional_int(row.get("season_number")),
            episode_number=optional_int(row.get("episode_number")),
            premiere_date=str(row.get("premiere_date") or ""),
            date_created=str(row.get("date_created") or ""),
            last_played=str(row.get("last_played") or ""),
            resume_ticks=int(row.get("resume_ticks") or 0),
            info_lines=[str(line) for line in row.get("info_lines", [])],
            subtitle_tracks=cached_subtitles,
        )
    except (KeyError, TypeError, ValueError):
        return None


def load_item_cache(path: Path, cfg: Config, user_id: str) -> list[MediaItem]:
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read item cache {path}: {exc}", file=sys.stderr)
        return []

    if data.get("cache_version") != CACHE_VERSION:
        return []

    if data.get("server_url") != cfg.jellyfin_url:
        return []

    if data.get("user_id") != user_id:
        return []

    items = []
    for row in data.get("items", []):
        if not isinstance(row, dict):
            continue
        item = media_item_from_cache(row)
        if item is not None:
            items.append(item)

    return items


def fake_cache_data_path() -> Path:
    plain_path = script_dir() / "tools" / "fake_cache_data.json"
    compressed_path = plain_path.with_suffix(plain_path.suffix + ".zst")
    return compressed_path if compressed_path.exists() else plain_path


def load_fake_cache_data() -> dict[str, Any]:
    path = fake_cache_data_path()
    try:
        if path.suffix == ".zst":
            result = subprocess.run(
                ["zstd", "--decompress", "--quiet", "--stdout", str(path)],
                check=True,
                capture_output=True,
            )
            data = json.loads(result.stdout)
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if path.exists():
            die("zstd is required to read compressed fake cache data")
        die(f"Missing fake cache data {path}")
    except subprocess.CalledProcessError as exc:
        die(f"Could not decompress fake cache data {path}: {exc}")
    except OSError as exc:
        die(f"Could not read fake cache data {path}: {exc}")
    except json.JSONDecodeError as exc:
        die(f"Could not parse fake cache data {path}: {exc}")

    if not isinstance(data, dict):
        die(f"Fake cache data {path} must contain a JSON object")
    return data


def load_fake_items() -> list[MediaItem]:
    path = fake_cache_data_path()
    data = load_fake_cache_data()

    items = []
    for row in data.get("items", []):
        if not isinstance(row, dict):
            continue
        item = media_item_from_cache(row)
        if item is not None:
            items.append(item)

    if not items:
        die(f"No valid fake items found in {path}")
    return items


def write_item_cache(path: Path, cfg: Config, user_id: str, items: list[MediaItem]) -> None:
    data = {
        "cache_version": CACHE_VERSION,
        "server_url": cfg.jellyfin_url,
        "user_id": user_id,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "items": [media_item_to_cache(item) for item in items],
    }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        print(f"Could not write item cache {path}: {exc}", file=sys.stderr)


class ItemPane(Static, can_focus=True):
    """A cheap list view: one widget, many rendered text lines."""
    pass


class BrowseApp(App[object]):
    CSS = ""

    def __init__(
        self,
        cfg: Config,
        client: JellyfinClient,
        items: list[MediaItem],
        theme_name: str,
        ui_state: UIState,
        write_cache_on_start: bool = True,
        auto_refresh_on_start: bool = False,
        last_refresh_started_at: Optional[float] = None,
        playback_manager: Optional["PlaybackManager"] = None,
        last_mpv_command: str = "",
        last_mpv_output: str = "",
    ):
        super().__init__()
        self.cfg = cfg
        self.client = client
        self.ui_state = ui_state
        self.write_cache = write_cache_on_start

        if self.write_cache:
            user_id = self.client.auth.user_id if self.client.auth is not None else ""
            write_item_cache(default_item_cache_path(), self.cfg, user_id, items)

        self.all_items_raw = items
        self.views = sorted_views(items)
        self.view = ui_state.view or cfg.initial_view
        self.display_mode = ui_state.display_mode or cfg.display_mode
        self.theme_name = theme_name
        self.all_count = len(items)
        self.filtered_items: list[MediaItem] = []
        self.visible_items: list[MediaItem] = []
        self.selected_index = 0
        self.scroll_offset = ui_state.scroll_offset
        self.regex_error = ""
        self.page = ui_state.page if ui_state.page in {"browser", "help", "info", "subtitles", "mpv_log"} else "browser"
        self.previous_page = ui_state.previous_page if ui_state.previous_page in {"browser", "info"} else "browser"
        self.info_scroll = ui_state.info_scroll
        self.mpv_log_scroll = ui_state.mpv_log_scroll
        self.playback_manager = playback_manager or PlaybackManager(client)
        self.playback_was_active = self.playback_manager.is_active()
        self.last_mpv_command = last_mpv_command
        self.last_mpv_output = last_mpv_output
        self.info_item: Optional[MediaItem] = find_item_by_id(items, ui_state.info_item_id)
        if self.page == "info" and self.info_item is None:
            self.page = "browser"
        if self.page == "subtitles" and self.info_item is None:
            self.page = "browser"
        self.subtitle_index = 0
        self.sort_desc = ui_state.sort_desc
        self._ignore_input_change = False
        self.auto_refresh_on_start = auto_refresh_on_start
        self.refreshing = False
        self.refresh_message = ""
        self.refresh_error = ""
        self.refresh_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.refresh_thread: Optional[threading.Thread] = None
        now = time.monotonic()
        self.last_activity_at = now
        self.last_refresh_started_at = last_refresh_started_at if last_refresh_started_at is not None else now

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("", id="top_status")
            yield Input(id="query")
            yield ItemPane("", id="items")
            yield Label("", id="bottom_status")

    @property
    def query(self) -> Input:
        return self.query_one("#query", Input)

    @property
    def listbox(self) -> ItemPane:
        return self.query_one("#items", ItemPane)

    @property
    def status(self) -> Label:
        return self.query_one("#top_status", Label)

    @property
    def bottom_status(self) -> Label:
        return self.query_one("#bottom_status", Label)

    def on_mount(self) -> None:
        self._ignore_input_change = True
        self.query.value = self.ui_state.query
        self._ignore_input_change = False

        self.apply_filter(restore=True)

        if self.page == "mpv_log":
            self.render_mpv_log()
        elif self.page == "subtitles" and self.info_item is not None:
            self.render_subtitle_picker()
        elif self.page == "info" and self.info_item is not None:
            self.render_info()
        elif self.ui_state.focus == "list" and self.visible_items:
            self.listbox.focus()
            self.render_items()
        else:
            self.query.focus()
            self.render_items()

        if self.auto_refresh_on_start:
            self.start_background_refresh("startup")

        self.start_periodic_refresh_check()
        self.maybe_start_periodic_refresh("startup")
        self.start_playback_poll()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.note_activity()
        if self._ignore_input_change:
            return
        self.apply_filter()

    def on_mouse_down(self, event) -> None:
        self.note_activity()

    def on_mouse_scroll_down(self, event) -> None:
        self.note_activity()

    def on_mouse_scroll_up(self, event) -> None:
        self.note_activity()

    def current_selected_item_id(self) -> str:
        if not self.visible_items:
            return ""

        self.selected_index = max(0, min(self.selected_index, len(self.visible_items) - 1))
        return self.visible_items[self.selected_index].id

    def focus_overlay(self) -> None:
        self.query.disabled = True
        if self.focused is not self.listbox:
            self.listbox.focus()

    def save_ui_state(self) -> None:
        self.ui_state.view = self.view
        self.ui_state.display_mode = self.display_mode
        self.ui_state.sort_desc = self.sort_desc
        self.ui_state.query = self.query.value
        self.ui_state.selected_item_id = self.current_selected_item_id()
        self.ui_state.scroll_offset = self.scroll_offset
        self.ui_state.focus = "list" if self.focused is self.listbox else "query"
        self.ui_state.page = self.page
        self.ui_state.previous_page = self.previous_page
        self.ui_state.info_item_id = self.info_item.id if self.info_item is not None else ""
        self.ui_state.info_scroll = self.info_scroll
        self.ui_state.mpv_log_scroll = self.mpv_log_scroll

    def subtitle_options(self, item: MediaItem) -> list[tuple[str, str]]:
        options = [
            ("auto", "auto"),
            ("none", "none"),
        ]

        options.extend((track.key, track.title) for track in item.subtitle_tracks)
        return options

    def subtitle_choice(self, item: MediaItem) -> str:
        choice = self.ui_state.subtitle_choices.get(item.id, "auto")
        valid = {key for key, _label in self.subtitle_options(item)}

        if choice in valid:
            return choice

        self.ui_state.subtitle_choices.pop(item.id, None)
        return "auto"

    def subtitle_choice_label(self, item: MediaItem) -> str:
        choice = self.subtitle_choice(item)

        for key, label in self.subtitle_options(item):
            if key == choice:
                return label

        return "auto"

    def bottom_status_text(self, prefix: str = "") -> str:
        parts = []

        if prefix:
            parts.append(prefix)
        playback = self.playback_manager.snapshot()
        if playback["active"]:
            title = playback["title"] or "mpv"
            parts.append(f"playing: {title}")
        if self.refreshing:
            parts.append(self.refresh_message or "refreshing...")
        elif self.refresh_error:
            parts.append(self.refresh_error)
        elif self.refresh_message:
            parts.append(self.refresh_message)

        parts.append(f"style: {self.theme_name}")
        return " | ".join(parts)

    def update_subtitle_status(self) -> None:
        prefix = ""
        if self.info_item is not None:
            prefix = f"subtitle: {self.subtitle_choice_label(self.info_item)}"

        self.bottom_status.update(self.bottom_status_text(prefix))

    def playback_request(self, item: MediaItem) -> PlaybackRequest:
        return PlaybackRequest(item=item, subtitle_choice=self.subtitle_choice(item))

    def play_selected(self) -> None:
        if not self.visible_items:
            return
        self.start_playback(self.visible_items[self.selected_index])

    def play_info_item(self) -> None:
        if self.info_item is None:
            return
        self.start_playback(self.info_item)

    def start_playback(self, item: MediaItem) -> None:
        self.save_ui_state()
        error = self.playback_manager.start_background(item, self.subtitle_choice(item))
        if error:
            self.refresh_error = error
        else:
            self.refresh_error = ""
            self.playback_was_active = True

        self.update_bottom_status()
        self.render_items()

    def on_key(self, event) -> None:
        self.note_activity()

        if event.key in {"ctrl+c", "ctrl+q"}:
            self.save_ui_state()
            self.exit(None)
            event.stop()
            return

        if event.key == "ctrl+r":
            self.start_background_refresh("manual")
            event.stop()
            return

        if event.key == "ctrl+g":
            self.open_mpv_log()
            event.stop()
            return

        if event.key == "ctrl+x":
            self.save_ui_state()
            self.exit(ThemeCycle())
            event.stop()
            return

        if self.page == "mpv_log":
            if event.key in {"q", "escape", "backspace"} or getattr(event, "character", None) == "q":
                self.page = self.previous_page
                self.render_items()
                event.stop()
                return

            if event.key in {"up", "down", "pageup", "pagedown", "home", "end"}:
                self.scroll_mpv_log(event.key)
                event.stop()
                return

            event.stop()
            return

        if self.page == "help":
            self.page = self.previous_page
            self.render_items()
            event.stop()
            return

        if self.page == "subtitles":
            if event.key in {"q", "escape", "backspace"} or getattr(event, "character", None) == "q":
                self.page = "info"
                self.render_info()
                event.stop()
                return

            if event.key == "enter":
                self.apply_subtitle_choice()
                event.stop()
                return

            if event.key in {"up", "down", "home", "end"}:
                self.move_subtitle_selection(event.key)
                event.stop()
                return

            event.stop()
            return

        if self.page == "info":
            typed = getattr(event, "character", None)

            if event.key in {"q", "escape", "backspace"} or typed == "q":
                self.page = "browser"
                self.render_items()
                self.query.focus()
                event.stop()
                return

            if event.key == "enter":
                self.play_info_item()
                event.stop()
                return

            if typed == "s" or event.key == "s":
                self.open_subtitle_picker()
                event.stop()
                return

            if event.key in {"left", "right"}:
                self.navigate_info_episode(1 if event.key == "right" else -1)
                event.stop()
                return

            if typed in {"[", "]"}:
                self.navigate_info_season(1 if typed == "]" else -1)
                event.stop()
                return

            if event.key in {"up", "down", "pageup", "pagedown", "home", "end"}:
                self.scroll_info(event.key)
                event.stop()
                return

            event.stop()
            return

        if event.key in {"ctrl+l", "f1"} or getattr(event, "character", None) == "?":
            self.previous_page = self.page if self.page in {"browser", "info"} else "browser"
            self.page = "help"
            self.render_help()
            event.stop()
            return

        if event.key == "ctrl+t":
            self.toggle_display_mode()
            event.stop()
            return

        if event.key == "ctrl+o":
            self.toggle_sort_order()
            event.stop()
            return

        # Do this manually because Tab can be swallowed by focus handling.
        if event.key == "tab":
            self.cycle_sort_mode(1)
            event.stop()
            return

        if self.focused is self.query and event.key == "down":
            if self.visible_items:
                self.selected_index = min(self.selected_index, len(self.visible_items) - 1)
                self.listbox.focus()
                self.ensure_selection_visible()
                self.render_items()
                event.stop()
            return

        if self.focused is self.listbox:
            if event.key in {"left", "right"}:
                self.cycle_sort_mode(1 if event.key == "right" else -1)
                event.stop()
                return

            if event.key == "shift+enter":
                self.play_selected()
                event.stop()
                return

            if event.key == "enter":
                self.open_info()
                event.stop()
                return

            if event.key == "up":
                if self.selected_index <= 0:
                    self.query.focus()
                    self.render_items()
                else:
                    self.selected_index -= 1
                    self.ensure_selection_visible()
                    self.render_items()
                event.stop()
                return

            if event.key == "down":
                if self.selected_index < len(self.visible_items) - 1:
                    self.selected_index += 1
                    self.ensure_selection_visible()
                    self.render_items()
                event.stop()
                return

            if event.key == "home":
                self.selected_index = 0
                self.ensure_selection_visible()
                self.render_items()
                event.stop()
                return

            if event.key == "end":
                if self.visible_items:
                    self.selected_index = len(self.visible_items) - 1
                    self.ensure_selection_visible()
                    self.render_items()
                event.stop()
                return

            if event.key in {"pageup", "pagedown"}:
                step = max(1, self.viewport_height() - 1)
                if event.key == "pageup":
                    self.selected_index = max(0, self.selected_index - step)
                else:
                    self.selected_index = min(len(self.visible_items) - 1, self.selected_index + step)
                self.ensure_selection_visible()
                self.render_items()
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

    def action_clear_search(self) -> None:
        self.query.value = ""
        self.query.focus()

    def overlay_panel(self, body: Text, title: str) -> Align:
        panel = Panel(
            body,
            title=title,
            border_style="dim",
            padding=(1, 2),
            expand=False,
        )
        return Align.center(panel, vertical="middle")

    def start_background_refresh(self, reason: str) -> None:
        if self.refreshing:
            self.refresh_message = "refresh already running"
            self.update_bottom_status()
            return

        self.last_refresh_started_at = time.monotonic()
        self.refreshing = True
        self.refresh_error = ""
        self.refresh_message = "refreshing..."
        self.update_bottom_status()

        self.refresh_thread = threading.Thread(
            target=self.refresh_worker,
            name="jbrowse-refresh",
            daemon=True,
            args=(reason,),
        )
        self.refresh_thread.start()
        self.set_timer(0.1, self.poll_refresh_result)

    def start_periodic_refresh_check(self) -> None:
        if self.cfg.refresh_interval_minutes <= 0:
            return

        self.set_timer(REFRESH_CHECK_SECONDS, self.check_periodic_refresh)

    def start_playback_poll(self) -> None:
        self.set_timer(0.5, self.poll_playback_status)

    def poll_playback_status(self) -> None:
        playback_active = self.playback_manager.is_active()

        if self.playback_was_active and not playback_active:
            self.refresh_message = "playback ended"
            if not self.refreshing:
                self.start_background_refresh("playback")

        self.playback_was_active = playback_active

        if self.page == "mpv_log":
            self.render_mpv_log()
        else:
            self.update_bottom_status()

        self.start_playback_poll()

    def check_periodic_refresh(self) -> None:
        self.maybe_start_periodic_refresh("periodic")
        self.start_periodic_refresh_check()

    def note_activity(self) -> None:
        self.last_activity_at = time.monotonic()
        self.maybe_start_periodic_refresh("activity")

    def is_refresh_due(self) -> bool:
        if self.cfg.refresh_interval_minutes <= 0:
            return False

        elapsed = time.monotonic() - self.last_refresh_started_at
        return elapsed >= self.cfg.refresh_interval_minutes * 60

    def is_recently_active(self) -> bool:
        return time.monotonic() - self.last_activity_at <= REFRESH_ACTIVE_WINDOW_SECONDS

    def maybe_start_periodic_refresh(self, reason: str) -> None:
        if self.refreshing:
            return
        if self.playback_manager.is_active():
            return
        if not self.is_refresh_due():
            return
        if not self.is_recently_active():
            return

        self.start_background_refresh(reason)

    def refresh_worker(self, reason: str) -> None:
        try:
            items = self.client.fetch_items()
        except JellyfinError as exc:
            self.refresh_queue.put(("error", str(exc)))
            return

        user_id = self.client.auth.user_id if self.client.auth is not None else ""
        if self.write_cache:
            write_item_cache(default_item_cache_path(), self.cfg, user_id, items)
        self.refresh_queue.put(("ok", items))

    def poll_refresh_result(self) -> None:
        try:
            status, payload = self.refresh_queue.get_nowait()
        except queue.Empty:
            if self.refreshing:
                self.set_timer(0.1, self.poll_refresh_result)
            return

        self.refreshing = False
        self.refresh_message = ""

        if status == "error":
            self.refresh_error = f"refresh failed: {payload}"
            self.update_bottom_status()
            return

        self.refresh_error = ""
        self.apply_refreshed_items(payload)

    def apply_refreshed_items(self, items: list[MediaItem]) -> None:
        selected_id = self.current_selected_item_id()
        old_scroll_offset = self.scroll_offset
        info_item_id = self.info_item.id if self.info_item is not None else ""
        old_info_scroll = self.info_scroll

        self.all_items_raw = items
        self.views = sorted_views(items)
        self.all_count = len(items)
        self.ui_state.selected_item_id = selected_id
        self.ui_state.scroll_offset = old_scroll_offset
        if info_item_id:
            self.info_item = find_item_by_id(items, info_item_id) or self.info_item
        self.info_scroll = old_info_scroll
        self.refresh_message = f"refreshed {len(items)} items"
        self.apply_filter(restore=True)

    def cycle_sort_mode(self, direction: int = 1) -> None:
        try:
            index = SORT_MODE_ORDER.index(self.view)
        except ValueError:
            index = 0

        self.view = SORT_MODE_ORDER[(index + direction) % len(SORT_MODE_ORDER)]
        persist_sort_state(self.cfg, self.view, self.sort_desc)
        self.apply_filter()

    def toggle_display_mode(self) -> None:
        self.display_mode = "filename" if self.display_mode == "title" else "title"
        persist_display_mode(self.cfg, self.display_mode)
        self.apply_filter()

    def toggle_sort_order(self) -> None:
        self.sort_desc = not self.sort_desc
        persist_sort_state(self.cfg, self.view, self.sort_desc)
        self.apply_filter()

    def item_text(self, item: MediaItem) -> str:
        if self.display_mode == "filename":
            return item.filename
        return item.title

    def apply_filter(self, restore: bool = False) -> None:
        text = self.query.value.strip()
        self.regex_error = ""

        source = self.views[self.view] if self.sort_desc else list(reversed(self.views[self.view]))

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
                    matched = [item for item in source if regex.search(self.item_text(item))]
        else:
            needle = text.casefold()
            matched = [item for item in source if needle in self.item_text(item).casefold()]

        selected_id = self.ui_state.selected_item_id if restore else self.current_selected_item_id()

        self.filtered_items = matched
        self.visible_items = matched[: self.cfg.max_display_items] if self.cfg.max_display_items else matched

        self.selected_index = 0
        if selected_id:
            for index, item in enumerate(self.visible_items):
                if item.id == selected_id:
                    self.selected_index = index
                    break

        if restore:
            self.scroll_offset = self.ui_state.scroll_offset
        else:
            self.scroll_offset = 0

        self.render_items()
        self.update_status()

    def viewport_height(self) -> int:
        height = getattr(self.listbox.size, "height", 0)
        return max(1, height or 20)

    def ensure_selection_visible(self) -> None:
        if not self.visible_items:
            self.selected_index = 0
            self.scroll_offset = 0
            return

        self.selected_index = max(0, min(self.selected_index, len(self.visible_items) - 1))
        height = self.viewport_height()

        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + height:
            self.scroll_offset = self.selected_index - height + 1

        max_offset = max(0, len(self.visible_items) - height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def open_info(self) -> None:
        if not self.visible_items:
            self.info_item = None
        else:
            self.info_item = self.visible_items[self.selected_index]

        self.page = "info"
        self.info_scroll = 0
        self.render_info()

    def info_series_items(self) -> list[MediaItem]:
        if self.info_item is None:
            return []

        item = self.info_item

        if item.kind != "Episode" or not item.series_name:
            return []

        items = [
            candidate
            for candidate in self.all_items_raw
            if candidate.kind == "Episode" and candidate.series_name == item.series_name
        ]

        return sorted(
            items,
            key=lambda candidate: (
                candidate.season_number if candidate.season_number is not None else 9999,
                candidate.episode_number if candidate.episode_number is not None else 9999,
                parse_jf_date(candidate.date_created),
            ),
        )

    def info_series_position(self) -> tuple[int, int]:
        items = self.info_series_items()

        if not items or self.info_item is None:
            return (0, 0)

        for index, item in enumerate(items):
            if item.id == self.info_item.id:
                return (index + 1, len(items))

        return (0, len(items))

    def navigate_info_episode(self, direction: int) -> None:
        items = self.info_series_items()

        if not items or self.info_item is None:
            return

        current_index = 0
        for index, item in enumerate(items):
            if item.id == self.info_item.id:
                current_index = index
                break

        new_index = max(0, min(len(items) - 1, current_index + direction))
        self.info_item = items[new_index]
        self.info_scroll = 0
        self.render_info()

    def navigate_info_season(self, direction: int) -> None:
        items = self.info_series_items()

        if not items or self.info_item is None or self.info_item.season_number is None:
            return

        seasons = sorted({
            item.season_number for item in items if item.season_number is not None
        })

        if not seasons:
            return

        try:
            current_season_index = seasons.index(self.info_item.season_number)
        except ValueError:
            current_season_index = 0

        new_season_index = max(0, min(len(seasons) - 1, current_season_index + direction))
        new_season = seasons[new_season_index]

        season_items = [item for item in items if item.season_number == new_season]
        if not season_items:
            return

        # Jump to the first episode of the target season.
        self.info_item = season_items[0]
        self.info_scroll = 0
        self.render_info()

    def open_subtitle_picker(self) -> None:
        if self.info_item is None:
            return

        current = self.subtitle_choice(self.info_item)
        options = self.subtitle_options(self.info_item)
        self.subtitle_index = 0

        for index, (key, _label) in enumerate(options):
            if key == current:
                self.subtitle_index = index
                break

        self.page = "subtitles"
        self.render_subtitle_picker()

    def move_subtitle_selection(self, key: str) -> None:
        if self.info_item is None:
            return

        options = self.subtitle_options(self.info_item)
        if not options:
            self.subtitle_index = 0
            return

        if key == "up":
            self.subtitle_index -= 1
        elif key == "down":
            self.subtitle_index += 1
        elif key == "home":
            self.subtitle_index = 0
        elif key == "end":
            self.subtitle_index = len(options) - 1

        self.subtitle_index = max(0, min(self.subtitle_index, len(options) - 1))
        self.render_subtitle_picker()

    def apply_subtitle_choice(self) -> None:
        if self.info_item is None:
            return

        options = self.subtitle_options(self.info_item)
        if not options:
            self.page = "info"
            self.render_info()
            return

        self.subtitle_index = max(0, min(self.subtitle_index, len(options) - 1))
        choice, _label = options[self.subtitle_index]

        if choice == "auto":
            self.ui_state.subtitle_choices.pop(self.info_item.id, None)
        else:
            self.ui_state.subtitle_choices[self.info_item.id] = choice

        self.page = "info"
        self.render_info()

    def render_subtitle_picker(self) -> None:
        self.focus_overlay()
        text = Text()

        if self.info_item is None:
            text.append("No selected item.", style="bold")
            self.listbox.update(self.overlay_panel(text, "Subtitles"))
            return

        options = self.subtitle_options(self.info_item)
        current = self.subtitle_choice(self.info_item)
        self.subtitle_index = max(0, min(self.subtitle_index, len(options) - 1))

        text.append("↑/↓ select | Enter apply | q/backspace cancel", style="dim")
        text.append("\n\n")

        for index, (key, label) in enumerate(options):
            if index:
                text.append("\n")

            prefix = "✓ " if key == current else "  "
            line = f"{prefix}{label}"

            if index == self.subtitle_index:
                text.append(line, style="reverse")
            elif key == current:
                text.append(line, style="bold")
            else:
                text.append(line)

        if not self.info_item.subtitle_tracks:
            text.append("\n\n")
            text.append("No subtitle tracks were reported by Jellyfin.", style="dim")

        self.update_subtitle_status()
        self.listbox.update(self.overlay_panel(text, "Subtitles"))

    def render_info(self) -> None:
        self.focus_overlay()
        info_text = Text()

        if self.info_item is None:
            lines = ["No selected item."]
        else:
            lines = self.info_item.info_lines

        height = max(8, self.viewport_height() - 4)
        max_scroll = max(0, len(lines) - height)
        self.info_scroll = max(0, min(self.info_scroll, max_scroll))

        shown = lines[self.info_scroll : self.info_scroll + height]

        info_text.append("q/backspace close | Enter play | s subtitles | ←/→ episode | [/] season | ↑/↓ scroll", style="dim")
        info_text.append("\n\n")

        for line_number, line in enumerate(shown):
            if line_number:
                info_text.append("\n")

            absolute_line = self.info_scroll + line_number

            if absolute_line == 0:
                info_text.append(line, style="bold")
            elif line and set(line) == {"-"}:
                info_text.append(line, style="dim")
            elif ":" in line and not line.startswith("/") and len(line.split(":", 1)[0]) < 24:
                label, value = line.split(":", 1)
                info_text.append(f"{label}:", style="bold")
                info_text.append(value)
            else:
                info_text.append(line)

        position, total = self.info_series_position()
        if total:
            info_title = f"Info {position}/{total}"
        else:
            info_title = "Info"

        self.update_subtitle_status()
        self.listbox.update(self.overlay_panel(info_text, info_title))

    def scroll_info(self, key: str) -> None:
        if self.info_item is None:
            return

        lines = self.info_item.info_lines
        height = max(8, self.viewport_height() - 4)
        max_scroll = max(0, len(lines) - height)

        if key == "up":
            self.info_scroll -= 1
        elif key == "down":
            self.info_scroll += 1
        elif key == "pageup":
            self.info_scroll -= height
        elif key == "pagedown":
            self.info_scroll += height
        elif key == "home":
            self.info_scroll = 0
        elif key == "end":
            self.info_scroll = max_scroll

        self.info_scroll = max(0, min(self.info_scroll, max_scroll))
        self.render_info()

    def open_mpv_log(self) -> None:
        if self.page in {"browser", "info"}:
            self.previous_page = self.page

        self.page = "mpv_log"
        self.mpv_log_scroll = 0
        self.render_mpv_log()

    def mpv_log_lines(self) -> list[str]:
        playback = self.playback_manager.snapshot()
        command = playback["command"] or self.last_mpv_command
        output = playback["output"] or self.last_mpv_output

        if not command:
            return [
                "No mpv command has been captured yet.",
                "",
                "Play something, then press Ctrl+G after mpv closes.",
            ]

        lines = [
            "Command",
            "-------",
            command,
            "",
            "Output",
            "------",
        ]

        if output.strip():
            lines.extend(output.splitlines())
        else:
            lines.append("(no output captured)")

        return lines

    def render_mpv_log(self) -> None:
        self.focus_overlay()
        lines = self.mpv_log_lines()
        height = max(8, self.viewport_height() - 4)
        max_scroll = max(0, len(lines) - height)
        self.mpv_log_scroll = max(0, min(self.mpv_log_scroll, max_scroll))
        shown = lines[self.mpv_log_scroll : self.mpv_log_scroll + height]

        text = Text()
        text.append("q/backspace close | ↑/↓ scroll | PageUp/PageDown | Home/End", style="dim")
        text.append("\n\n")

        for line_number, line in enumerate(shown):
            if line_number:
                text.append("\n")

            absolute_line = self.mpv_log_scroll + line_number
            if absolute_line in {0, 4} and line in {"Command", "Output"}:
                text.append(line, style="bold")
            elif line and set(line) == {"-"}:
                text.append(line, style="dim")
            else:
                text.append(line)

        self.listbox.update(self.overlay_panel(text, "mpv log"))

    def scroll_mpv_log(self, key: str) -> None:
        lines = self.mpv_log_lines()
        height = max(8, self.viewport_height() - 4)
        max_scroll = max(0, len(lines) - height)

        if key == "up":
            self.mpv_log_scroll -= 1
        elif key == "down":
            self.mpv_log_scroll += 1
        elif key == "pageup":
            self.mpv_log_scroll -= height
        elif key == "pagedown":
            self.mpv_log_scroll += height
        elif key == "home":
            self.mpv_log_scroll = 0
        elif key == "end":
            self.mpv_log_scroll = max_scroll

        self.mpv_log_scroll = max(0, min(self.mpv_log_scroll, max_scroll))
        self.render_mpv_log()

    def render_help(self) -> None:
        self.focus_overlay()
        help_text = Text()
        help_text.append("jbrowse hotkeys\n", style="bold")
        help_text.append("\n")
        help_text.append("Enter        show selected item info\n")
        help_text.append("Shift+Enter  play selected item immediately\n")
        help_text.append("Tab          next sort mode\n")
        help_text.append("Left/Right   previous/next sort mode while list is focused\n")
        help_text.append("Up/Down      move selection; Up at top returns to search\n")
        help_text.append("PageUp/Down  move by a page\n")
        help_text.append("Home/End     jump to first/last shown result\n")
        help_text.append("Typing       from list: return to search and keep typed char\n")
        help_text.append("Esc          clear search\n")
        help_text.append("/pattern     regex search\n")
        help_text.append("Ctrl+T       toggle title/filename display and search\n")
        help_text.append("Ctrl+O       toggle ascending/descending sort\n")
        help_text.append("Info: q/backspace close, Enter play, s subtitles, ←/→ episode, [/] season\n")
        help_text.append("Ctrl+R       refresh Jellyfin list\n")
        help_text.append("Ctrl+G       show last mpv output\n")
        help_text.append("Ctrl+X       cycle theme and save it to jbrowse.conf\n")
        help_text.append("Ctrl+L       show this help\n")
        help_text.append("F1 or ?      show this help too\n")
        help_text.append("Ctrl+C       quit\n")
        help_text.append("\n")
        help_text.append("Press any key to close this help.", style="dim")
        self.listbox.update(self.overlay_panel(help_text, "Help"))

    def render_items(self) -> None:
        if self.page == "help":
            self.render_help()
            return

        if self.page == "mpv_log":
            self.render_mpv_log()
            return

        if self.page == "info":
            self.render_info()
            return

        if self.page == "subtitles":
            self.render_subtitle_picker()
            return

        self.query.disabled = False
        self.ensure_selection_visible()

        height = self.viewport_height()
        start = self.scroll_offset
        end = min(len(self.visible_items), start + height)

        text = Text()

        for index in range(start, end):
            title = self.item_text(self.visible_items[index])

            if index == self.selected_index and self.focused is self.listbox:
                text.append(title, style="reverse")
            elif index == self.selected_index:
                text.append(title, style="bold")
            else:
                text.append(title)

            if index < end - 1:
                text.append("\n")

        self.listbox.update(text)

    def on_resize(self) -> None:
        self.render_items()

    def update_status(self) -> None:
        sort_label = SORT_MODE_LABELS.get(self.view, self.view)
        sort_arrow = "↓" if self.sort_desc else "↑"
        sort_text = f"sort: {sort_label:<14} {sort_arrow}"

        parts = [
            sort_text,
            f"{self.all_count} loaded",
            f"{len(self.filtered_items)} matched",
            f"showing {len(self.visible_items)}",
        ]

        if self.regex_error:
            parts.append(f"regex error: {self.regex_error}")

        parts.append(f"display: {self.display_mode}")
        parts.append("F1 help")

        self.status.update(" | ".join(parts))
        self.update_bottom_status()

    def update_bottom_status(self) -> None:
        if self.page in {"info", "subtitles"}:
            self.update_subtitle_status()
        else:
            self.bottom_status.update(self.bottom_status_text())


def subtitle_track_for_choice(item: MediaItem, choice: str) -> Optional[SubtitleTrack]:
    for track in item.subtitle_tracks:
        if track.key == choice:
            return track

    return None


def redact_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)

    if not parsed.scheme or not parsed.netloc:
        return value

    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_query = [
        (key, "REDACTED" if key.lower() in {"api_key", "apikey", "token", "access_token"} else item)
        for key, item in query
    ]

    return urllib.parse.urlunsplit(
        parsed._replace(query=urllib.parse.urlencode(redacted_query))
    )


def debug_mpv_command(args: list[str]) -> str:
    return shlex.join([redact_url(arg) for arg in args])


def expand_mpv_token(token: str, values: dict[str, str]) -> str:
    expanded = string.Template(token).safe_substitute(values)

    for name, value in values.items():
        expanded = expanded.replace(f"{{{name}}}", value)

    return expanded


def build_mpv_command(
    cfg: Config,
    item: MediaItem,
    url: str,
    subtitle_choice: str,
) -> tuple[list[str], Optional[SubtitleTrack]]:
    subtitle_track = subtitle_track_for_choice(item, subtitle_choice)
    subtitle_arg = ""
    start_arg = ""

    if subtitle_choice == "none":
        subtitle_arg = "--sid=no"
    elif subtitle_track is not None:
        subtitle_arg = f"--sid={subtitle_track.mpv_sid}"

    if item.resume_seconds > 0:
        start_arg = f"--start={item.resume_seconds:.3f}"

    values = {
        "url": url,
        "title": item.title,
        "filename": item.filename,
        "subtitle": subtitle_arg,
        "start": start_arg,
    }

    args: list[str] = []
    for token in cfg.mpv_cmd:
        if is_placeholder_token(token, "subtitle"):
            if subtitle_arg:
                args.append(subtitle_arg)
            continue

        if is_placeholder_token(token, "start"):
            if start_arg:
                args.append(start_arg)
            continue

        expanded = expand_mpv_token(token, values)
        if expanded:
            args.append(expanded)

    return (args, subtitle_track)


class PlaybackManager:
    def __init__(self, client: JellyfinClient):
        self.client = client
        self.started_at = 0.0
        self.item: Optional[MediaItem] = None
        self.play_session_id = ""
        self.process: Optional[subprocess.Popen] = None
        self.output_lines: list[str] = []
        self.last_command = ""
        self.last_return_code: Optional[int] = None
        self.lock = threading.Lock()

    def position_ticks(self) -> int:
        if self.item is None or self.started_at <= 0:
            return 0

        elapsed = max(0.0, time.monotonic() - self.started_at)
        return self.item.resume_ticks + int(elapsed * TICKS_PER_SECOND)

    def playback_payload(self, item: MediaItem, position_ticks: int) -> dict[str, Any]:
        return {
            "ItemId": item.id,
            "MediaSourceId": item.id,
            "PlaySessionId": self.play_session_id,
            "PositionTicks": max(0, position_ticks),
            "IsPaused": False,
            "IsMuted": False,
            "CanSeek": True,
            "PlayMethod": "DirectStream",
            "RepeatMode": "RepeatNone",
            "PlaybackRate": 1,
        }

    def report(self, label: str, reporter, item: MediaItem, position_ticks: int) -> None:
        try:
            reporter(self.playback_payload(item, position_ticks))
        except JellyfinError as exc:
            print(f"Jellyfin playback {label} report failed: {exc}", file=sys.stderr)

    def is_active(self) -> bool:
        with self.lock:
            return self.process is not None and self.process.poll() is None

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            active = self.process is not None and self.process.poll() is None
            title = self.item.filename if self.item is not None else ""
            return {
                "active": active,
                "title": title,
                "command": self.last_command,
                "output": "".join(self.output_lines),
                "return_code": self.last_return_code,
            }

    def append_output(self, text: str) -> None:
        if not text:
            return

        with self.lock:
            self.output_lines.append(text)
            if len(self.output_lines) > 2000:
                del self.output_lines[: len(self.output_lines) - 2000]

    def start_background(self, item: MediaItem, subtitle_choice: str = "auto") -> str:
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                return "mpv is already running"

        url = self.client.stream_url(item)
        args, subtitle_track = build_mpv_command(self.client.cfg, item, url, subtitle_choice)
        command = debug_mpv_command(args)

        if subtitle_choice == "none":
            subtitle_line = "Subtitles: none\n"
        elif subtitle_track is not None:
            subtitle_line = f"Subtitles: {subtitle_track.title}\n"
        else:
            subtitle_line = ""

        try:
            process = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
        except FileNotFoundError:
            return f"could not find mpv executable: {args[0]}"

        with self.lock:
            self.process = process
            self.item = item
            self.started_at = time.monotonic()
            self.play_session_id = secrets.token_hex(16)
            self.output_lines = [
                f"Now Playing: {item.filename}\n",
                subtitle_line,
                f"DEBUG mpv command: {command}\n",
            ]
            self.last_command = command
            self.last_return_code = None

        self.report("start", self.client.report_playback_started, item, item.resume_ticks)

        reader = threading.Thread(
            target=self.read_output_worker,
            name="jbrowse-mpv-output",
            daemon=True,
            args=(process,),
        )
        waiter = threading.Thread(
            target=self.wait_for_background_playback,
            name="jbrowse-mpv-wait",
            daemon=True,
            args=(process, item),
        )
        reader.start()
        waiter.start()
        return ""

    def read_output_worker(self, process: subprocess.Popen) -> None:
        if process.stdout is None:
            return

        try:
            for line in process.stdout:
                self.append_output(line)
        except ValueError:
            return

    def wait_for_background_playback(self, process: subprocess.Popen, item: MediaItem) -> None:
        return_code = process.wait()
        final_position = self.position_ticks()
        self.report("progress", self.client.report_playback_progress, item, final_position)
        self.report("stopped", self.client.report_playback_stopped, item, final_position)

        with self.lock:
            if self.process is process:
                self.last_return_code = return_code
                self.process = None
                self.item = None
                self.started_at = 0.0
                self.play_session_id = ""

    def run(self, item: MediaItem, subtitle_choice: str = "auto") -> PlaybackResult:
        url = self.client.stream_url(item)
        args, subtitle_track = build_mpv_command(self.client.cfg, item, url, subtitle_choice)
        command = debug_mpv_command(args)

        print(f"Now Playing: \033[1;32m{item.filename}\033[0m")
        if subtitle_choice == "none":
            print("Subtitles: none")
        elif subtitle_track is not None:
            print(f"Subtitles: {subtitle_track.title}")

        print(f"DEBUG mpv command: {command}", file=sys.stderr)

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
        except FileNotFoundError:
            die(f"Could not find mpv executable: {args[0]}")
            return PlaybackResult(1, command, "")

        self.item = item
        self.started_at = time.monotonic()
        self.play_session_id = secrets.token_hex(16)
        self.report("start", self.client.report_playback_started, item, item.resume_ticks)

        output = ""
        try:
            output, _unused = process.communicate()
            return_code = process.returncode or 0
        except KeyboardInterrupt:
            if process.poll() is None:
                process.terminate()
                try:
                    output, _unused = process.communicate(timeout=5)
                    return_code = process.returncode or 130
                except subprocess.TimeoutExpired:
                    process.kill()
                    output, _unused = process.communicate()
                    return_code = process.returncode or 130
            else:
                return_code = process.returncode or 130
        finally:
            final_position = self.position_ticks()
            self.report("progress", self.client.report_playback_progress, item, final_position)
            self.report("stopped", self.client.report_playback_stopped, item, final_position)
            self.item = None
            self.started_at = 0.0
            self.play_session_id = ""

        return PlaybackResult(return_code, command, output or "")


def play_item(client: JellyfinClient, item: MediaItem, subtitle_choice: str = "auto") -> PlaybackResult:
    return PlaybackManager(client).run(item, subtitle_choice)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny Jellyfin TUI launcher for mpv")
    parser.add_argument("--config", help="override config path")
    parser.add_argument("--state", help="override state path")
    parser.add_argument("--style", help="override Textual CSS style path")
    parser.add_argument("--fake", action="store_true", help="browse fake cache data without Jellyfin")
    parser.add_argument("--print-config-path", action="store_true")
    parser.add_argument("--print-state-path", action="store_true")
    parser.add_argument("--print-style-path", action="store_true")
    return parser.parse_args()


def browser_loop(
    cfg: Config,
    client: JellyfinClient,
    items: list[MediaItem],
    themes: list[Theme],
    auto_refresh_on_start: bool,
    last_refresh_started_at: float,
    write_cache: bool = True,
    persist_theme: bool = True,
) -> int:
    theme_index = 0
    ui_state = UIState(view=cfg.sort_mode, display_mode=cfg.display_mode, sort_desc=cfg.sort_desc)
    playback_manager = PlaybackManager(client)
    last_mpv_command = ""
    last_mpv_output = ""

    while True:
        theme = themes[theme_index]
        BrowseApp.CSS = theme.tcss

        app = BrowseApp(
            cfg,
            client,
            items,
            theme.name,
            ui_state,
            write_cache_on_start=write_cache,
            auto_refresh_on_start=auto_refresh_on_start,
            last_refresh_started_at=last_refresh_started_at,
            playback_manager=playback_manager,
            last_mpv_command=last_mpv_command,
            last_mpv_output=last_mpv_output,
        )
        chosen = app.run()
        items = app.all_items_raw
        last_refresh_started_at = app.last_refresh_started_at
        auto_refresh_on_start = False

        if chosen is None:
            return 0

        if isinstance(chosen, ThemeCycle):
            theme_index = (theme_index + 1) % len(themes)
            if persist_theme:
                persist_style_path(cfg, themes[theme_index])
            print(f"Theme: {themes[theme_index].name}", file=sys.stderr)
            continue

        if isinstance(chosen, PlaybackRequest):
            result = play_item(client, chosen.item, chosen.subtitle_choice)
            last_mpv_command = result.command
            last_mpv_output = result.output
            auto_refresh_on_start = True


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

    cli_style_path = Path(args.style).expanduser() if args.style else None
    starting_style = initial_theme(cli_style_path or cfg.style_path)

    if args.print_style_path:
        print(starting_style.path if starting_style.path is not None else "built-in")
        return 0

    themes = discover_themes(starting_style)

    print(f"Using config: {cfg.path}", file=sys.stderr)
    print(f"Using style: {starting_style.name}", file=sys.stderr)
    print(f"Discovered themes: {len(themes)}", file=sys.stderr)
    if args.fake:
        items = load_fake_items()
        client = FakeJellyfinClient(cfg, items)
        auto_refresh_on_start = False
        print(f"Using {len(items)} fake items from {fake_cache_data_path()}.", file=sys.stderr)
    else:
        state = load_state(state_path)
        client = JellyfinClient(cfg, state)
        item_cache_path = default_item_cache_path()

        print(f"Using state: {state.path}", file=sys.stderr)
        print(f"Using item cache: {item_cache_path}", file=sys.stderr)
        print("Logging into Jellyfin...", file=sys.stderr)
        try:
            client.login()
        except JellyfinError as exc:
            die(f"Jellyfin error: {exc}")

        user_id = client.auth.user_id if client.auth is not None else ""
        items = load_item_cache(item_cache_path, cfg, user_id)
        auto_refresh_on_start = bool(items)

        if items:
            print(f"Loaded {len(items)} cached items.", file=sys.stderr)
        else:
            print("Fetching Jellyfin library...", file=sys.stderr)
            try:
                items = client.fetch_items()
            except JellyfinError as exc:
                die(f"Jellyfin error: {exc}")
            write_item_cache(item_cache_path, cfg, user_id, items)

    if not items:
        die("No playable Jellyfin items found.")

    return browser_loop(
        cfg,
        client,
        items,
        themes,
        auto_refresh_on_start,
        time.monotonic(),
        write_cache=not args.fake,
        persist_theme=not args.fake,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
