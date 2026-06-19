#!/usr/bin/env python3
"""
Tiny real-terminal screenshot POC.

What it does:
1. Open the real jbrowse app in GNOME Terminal/Xwayland.
2. Take one screenshot.
3. Send literal Ctrl+X.
4. Take one more screenshot.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def log(message: str) -> None:
    print(f"[screenshot-poc] {message}", file=sys.stderr)


def require(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"missing command: {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Take two real-terminal jbrowse screenshots")
    parser.add_argument("--output", default="screenshot/poc", help="output directory")
    parser.add_argument("--geometry", default="120x36", help="GNOME Terminal geometry")
    parser.add_argument("--settle", type=float, default=7.0, help="seconds to wait after opening")
    parser.add_argument("--after-key", type=float, default=8.0, help="seconds to wait after Ctrl+X")
    return parser.parse_args()


def launch_terminal(title: str, geometry: str) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env["GDK_BACKEND"] = "x11"
    return subprocess.Popen(
        [
            "dbus-run-session",
            "--",
            "gnome-terminal",
            "--wait",
            f"--title={title}",
            f"--geometry={geometry}",
            f"--working-directory={ROOT}",
            "--",
            sys.executable,
            str(ROOT / "jbrowse.py"),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def find_window(title: str, timeout: float = 12.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--name", title],
            capture_output=True,
            text=True,
            check=False,
        )
        window_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if window_ids:
            return window_ids[-1]
        time.sleep(0.1)

    raise RuntimeError("could not find GNOME Terminal window")


def send_key(window_id: str, key: str) -> None:
    subprocess.run(["xdotool", "windowactivate", "--sync", window_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    time.sleep(0.1)
    subprocess.run(["xdotool", "key", key], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def screenshot(window_id: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    converter = "magick" if shutil.which("magick") else "convert"
    xwd = subprocess.Popen(["xwd", "-silent", "-frame", "-id", window_id], stdout=subprocess.PIPE)
    try:
        subprocess.run([converter, "xwd:-", str(path)], stdin=xwd.stdout, check=True)
    finally:
        if xwd.stdout is not None:
            xwd.stdout.close()
        xwd.wait(timeout=5)


def main() -> int:
    args = parse_args()
    for command in ["dbus-run-session", "gnome-terminal", "xdotool", "xwd"]:
        require(command)
    if shutil.which("magick") is None and shutil.which("convert") is None:
        raise RuntimeError("missing command: magick or convert")

    output = Path(args.output).expanduser()
    title = f"jbrowse-screenshot-poc-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    process = launch_terminal(title, args.geometry)

    try:
        window_id = find_window(title)
        log("waiting for jbrowse to open")
        time.sleep(args.settle)

        log("capturing before.png")
        screenshot(window_id, output / "before.png")

        log("sending Ctrl+X")
        send_key(window_id, "ctrl+x")
        time.sleep(args.after_key)
        window_id = find_window(title)

        log("capturing after-ctrl-x.png")
        screenshot(window_id, output / "after-ctrl-x.png")
        log(f"saved screenshots to {output}")
        return 0
    finally:
        if process.poll() is None:
            try:
                send_key(find_window(title, timeout=1.0), "ctrl+c")
            except (RuntimeError, subprocess.CalledProcessError):
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
