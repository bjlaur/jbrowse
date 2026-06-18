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
  Ctrl+X cycles discovered .tcss files.

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
import os
import re
import secrets
import socket
import subprocess
import sys
import textwrap
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
CLIENT_VERSION = "0.23"
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
        path = cfg_path.parent / path

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



def persist_display_mode(cfg: Config, display_mode: str) -> None:
    """Save the current title/filename display mode under [ui]."""
    parser = configparser.ConfigParser(strict=False)

    if cfg.path.exists():
        parser.read(cfg.path)

    if not parser.has_section("ui"):
        parser.add_section("ui")

    parser.set("ui", "display_mode", display_mode)

    try:
        with cfg.path.open("w", encoding="utf-8") as fh:
            parser.write(fh)
    except OSError as exc:
        print(f"Could not persist display mode to {cfg.path}: {exc}", file=sys.stderr)


@dataclasses.dataclass(frozen=True)
class Theme:
    name: str
    path: Optional[Path]
    tcss: str


class ThemeCycle:
    pass


class RefreshRequest:
    pass


@dataclasses.dataclass
class UIState:
    view: str = ""
    display_mode: str = ""
    sort_desc: bool = True
    query: str = ""
    selected_item_id: str = ""
    scroll_offset: int = 0
    focus: str = "query"
    info_visible: bool = False
    info_item_id: str = ""
    info_scroll: int = 0


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
        search_dirs = [start.path.parent, script_dir(), Path.home() / ".config" / APP_NAME]
    else:
        search_dirs = [script_dir(), Path.home() / ".config" / APP_NAME]

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
    max_display_items: int
    display_mode: str
    style_path: Optional[Path]


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
    date_created: str
    last_played: str
    resume_ticks: int
    info_lines: list[str]

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
        "initial_view = added\n"
        "max_display_items = 300\n"
        "# title or filename\n"
        "display_mode = title\n\n"
        "[style]\n"
        "# Optional. Relative paths are relative to jbrowse.conf.\n"
        "# path = jbrowse.tcss\n"
    )


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

    initial_view = parser.get("ui", "initial_view", fallback="added").strip().lower()
    if initial_view not in {"played", "added"}:
        die("ui.initial_view must be played or added")

    display_mode = parser.get("ui", "display_mode", fallback="title").strip().lower()
    if display_mode not in {"title", "filename"}:
        die("ui.display_mode must be title or filename")

    style_value = parser.get("style", "path", fallback="")
    style_path = expand_style_path(style_value, path)

    return Config(
        path=path,
        jellyfin_url=jellyfin_url,
        username=username,
        password=password,
        item_types=item_types,
        initial_view=initial_view,
        max_display_items=max(
            0,
            parser.getint("ui", "max_display_items", fallback=DEFAULT_VISIBLE_ITEMS),
        ),
        display_mode=display_mode,
        style_path=style_path,
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
                "Fields": "DateCreated,UserData,SeriesName,ParentIndexNumber,IndexNumber,ProductionYear,Path,MediaSources,Overview,Genres,OfficialRating,CommunityRating,PremiereDate,RunTimeTicks,ProviderIds",
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
        date_created=raw.get("DateCreated") or "",
        last_played=user_data.get("LastPlayedDate") or "",
        resume_ticks=int(user_data.get("PlaybackPositionTicks") or 0),
        info_lines=make_info_lines(raw, title, filename),
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
    }



def find_item_by_id(items: list[MediaItem], item_id: str) -> Optional[MediaItem]:
    if not item_id:
        return None

    for item in items:
        if item.id == item_id:
            return item

    return None


class ItemPane(Static, can_focus=True):
    """A cheap list view: one widget, many rendered text lines."""
    pass


class BrowseApp(App[object]):
    CSS = ""

    def __init__(self, cfg: Config, client: JellyfinClient, items: list[MediaItem], theme_name: str, ui_state: UIState):
        super().__init__()
        self.cfg = cfg
        self.client = client
        self.ui_state = ui_state
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
        self.help_visible = False
        self.info_visible = ui_state.info_visible
        self.info_scroll = ui_state.info_scroll
        self.info_item: Optional[MediaItem] = find_item_by_id(items, ui_state.info_item_id)
        self.sort_desc = ui_state.sort_desc
        self._ignore_input_change = False

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

        if self.info_visible and self.info_item is not None:
            self.render_info()
        elif self.ui_state.focus == "list" and self.visible_items:
            self.listbox.focus()
            self.render_items()
        else:
            self.query.focus()
            self.render_items()

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._ignore_input_change:
            return
        self.apply_filter()

    def current_selected_item_id(self) -> str:
        if not self.visible_items:
            return ""

        self.selected_index = max(0, min(self.selected_index, len(self.visible_items) - 1))
        return self.visible_items[self.selected_index].id

    def save_ui_state(self) -> None:
        self.ui_state.view = self.view
        self.ui_state.display_mode = self.display_mode
        self.ui_state.sort_desc = self.sort_desc
        self.ui_state.query = self.query.value
        self.ui_state.selected_item_id = self.current_selected_item_id()
        self.ui_state.scroll_offset = self.scroll_offset
        self.ui_state.focus = "list" if self.focused is self.listbox else "query"
        self.ui_state.info_visible = self.info_visible
        self.ui_state.info_item_id = self.info_item.id if self.info_item is not None else ""
        self.ui_state.info_scroll = self.info_scroll

    def play_selected(self) -> None:
        if not self.visible_items:
            return
        self.save_ui_state()
        self.exit(self.visible_items[self.selected_index])

    def play_info_item(self) -> None:
        if self.info_item is None:
            return
        self.save_ui_state()
        self.exit(self.info_item)

    def on_key(self, event) -> None:
        if event.key in {"ctrl+c", "ctrl+q"}:
            self.save_ui_state()
            self.exit(None)
            event.stop()
            return

        if self.help_visible:
            self.help_visible = False
            self.render_items()
            event.stop()
            return

        if self.info_visible:
            typed = getattr(event, "character", None)

            if event.key in {"q", "escape", "backspace"} or typed == "q":
                self.info_visible = False
                self.query.focus()
                self.render_items()
                event.stop()
                return

            if event.key == "enter":
                self.play_info_item()
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

            return

        if event.key in {"ctrl+l", "f1"} or getattr(event, "character", None) == "?":
            self.help_visible = True
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

        if event.key == "ctrl+r":
            self.show_refreshing()
            self.set_timer(0.01, self.refresh_from_jellyfin)
            event.stop()
            return

        if event.key == "ctrl+x":
            self.save_ui_state()
            self.exit(ThemeCycle())
            event.stop()
            return

        # Do this manually because Tab can be swallowed by focus handling.
        if event.key == "tab":
            self.toggle_view()
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
                self.toggle_view()
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

    def show_refreshing(self) -> None:
        text = Text()
        text.append("Refreshing Jellyfin state...", style="bold")
        text.append("\n\n")
        text.append("Please wait.", style="dim")
        self.listbox.update(self.overlay_panel(text, "Refresh"))
        self.status.update("refreshing...")
        self.bottom_status.update(f"style: {self.theme_name}")

    def refresh_from_jellyfin(self) -> None:
        try:
            items = self.client.fetch_items()
        except JellyfinError as exc:
            text = Text()
            text.append(f"Jellyfin refresh failed: {exc}", style="bold")
            text.append("\n\n")
            text.append("Press any key to continue.", style="dim")
            self.listbox.update(self.overlay_panel(text, "Refresh failed"))
            self.help_visible = True
            return

        self.all_items_raw = items
        self.views = sorted_views(items)
        self.all_count = len(items)
        self.selected_index = 0
        self.scroll_offset = 0
        self.apply_filter()

    def toggle_view(self) -> None:
        self.view = "added" if self.view == "played" else "played"
        self.apply_filter()

    def toggle_display_mode(self) -> None:
        self.display_mode = "filename" if self.display_mode == "title" else "title"
        persist_display_mode(self.cfg, self.display_mode)
        self.apply_filter()

    def toggle_sort_order(self) -> None:
        self.sort_desc = not self.sort_desc
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

        self.info_visible = True
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

    def render_info(self) -> None:
        info_text = Text()

        if self.info_item is None:
            lines = ["No selected item."]
        else:
            lines = self.info_item.info_lines

        height = max(8, self.viewport_height() - 4)
        max_scroll = max(0, len(lines) - height)
        self.info_scroll = max(0, min(self.info_scroll, max_scroll))

        shown = lines[self.info_scroll : self.info_scroll + height]

        info_text.append("q/backspace close | Enter play | ←/→ episode | [/] season | ↑/↓ scroll", style="dim")
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

    def render_help(self) -> None:
        help_text = Text()
        help_text.append("jbrowse hotkeys\n", style="bold")
        help_text.append("\n")
        help_text.append("Enter        show selected item info\n")
        help_text.append("Shift+Enter  play selected item immediately\n")
        help_text.append("Tab          toggle played/added\n")
        help_text.append("Left/Right   toggle played/added while list is focused\n")
        help_text.append("Up/Down      move selection; Up at top returns to search\n")
        help_text.append("PageUp/Down  move by a page\n")
        help_text.append("Home/End     jump to first/last shown result\n")
        help_text.append("Typing       from list: return to search and keep typed char\n")
        help_text.append("Esc          clear search\n")
        help_text.append("/pattern     regex search\n")
        help_text.append("Ctrl+T       toggle title/filename display and search\n")
        help_text.append("Ctrl+O       toggle ascending/descending sort\n")
        help_text.append("Info: q/backspace close, Enter play, ←/→ episode, [/] season\n")
        help_text.append("Ctrl+R       refresh Jellyfin list\n")
        help_text.append("Ctrl+X       cycle theme and save it to jbrowse.conf\n")
        help_text.append("Ctrl+L       show this help\n")
        help_text.append("F1 or ?      show this help too\n")
        help_text.append("Ctrl+C       quit\n")
        help_text.append("\n")
        help_text.append("Press any key to close this help.", style="dim")
        self.listbox.update(self.overlay_panel(help_text, "Help"))

    def render_items(self) -> None:
        if self.help_visible:
            self.render_help()
            return

        if self.info_visible:
            self.render_info()
            return

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
        sort_label = "last played" if self.view == "played" else "recently added"
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
        self.bottom_status.update(f"style: {self.theme_name}")


def play_item(client: JellyfinClient, item: MediaItem) -> int:
    url = client.stream_url(item)

    args = [
        "mpv",
        "--hwdec=auto",
        f"--force-media-title={item.filename}",
    ]

    if item.resume_seconds > 0:
        args.append(f"--start={item.resume_seconds:.3f}")

    args.append(url)

    print(f"Now Playing: \033[1;32m{item.filename}\033[0m")

    try:
        process = subprocess.Popen(args)
    except FileNotFoundError:
        die("Could not find mpv executable: mpv")
        return 1

    try:
        return process.wait()
    except KeyboardInterrupt:
        if process.poll() is None:
            process.terminate()
            try:
                return process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                return process.wait()
        return process.returncode or 130


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny Jellyfin TUI launcher for mpv")
    parser.add_argument("--config", help="override config path")
    parser.add_argument("--state", help="override state path")
    parser.add_argument("--style", help="override Textual CSS style path")
    parser.add_argument("--print-config-path", action="store_true")
    parser.add_argument("--print-state-path", action="store_true")
    parser.add_argument("--print-style-path", action="store_true")
    return parser.parse_args()


def browser_loop(cfg: Config, client: JellyfinClient, items: list[MediaItem], themes: list[Theme]) -> int:
    theme_index = 0
    ui_state = UIState(view=cfg.initial_view, display_mode=cfg.display_mode)

    while True:
        theme = themes[theme_index]
        BrowseApp.CSS = theme.tcss

        chosen = BrowseApp(cfg, client, items, theme.name, ui_state).run()

        if chosen is None:
            return 0

        if isinstance(chosen, ThemeCycle):
            theme_index = (theme_index + 1) % len(themes)
            persist_style_path(cfg, themes[theme_index])
            print(f"Theme: {themes[theme_index].name}", file=sys.stderr)
            continue

        if isinstance(chosen, RefreshRequest):
            print("Refreshing Jellyfin state...", file=sys.stderr)
            try:
                items = client.fetch_items()
            except JellyfinError as exc:
                print(f"Jellyfin refresh failed: {exc}", file=sys.stderr)
                print("Returning with old item list.", file=sys.stderr)
            continue

        play_item(client, chosen)


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

    state = load_state(state_path)
    client = JellyfinClient(cfg, state)

    print(f"Using config: {cfg.path}", file=sys.stderr)
    print(f"Using state: {state.path}", file=sys.stderr)
    print(f"Using style: {starting_style.name}", file=sys.stderr)
    print(f"Discovered themes: {len(themes)}", file=sys.stderr)
    print("Logging into Jellyfin...", file=sys.stderr)

    try:
        client.login()
        items = client.fetch_items()
    except JellyfinError as exc:
        die(f"Jellyfin error: {exc}")

    if not items:
        die("No playable Jellyfin items found.")

    return browser_loop(cfg, client, items, themes)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
