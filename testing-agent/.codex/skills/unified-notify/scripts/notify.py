#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import time


def is_vscode_env(env: dict) -> bool:
    if env.get("TERM_PROGRAM") == "vscode":
        return True
    return any(key.startswith("VSCODE_") for key in env.keys())


def is_iterm_env(env: dict) -> bool:
    return env.get("TERM_PROGRAM") == "iTerm.app" or "ITERM_SESSION_ID" in env


def is_terminal_env(env: dict) -> bool:
    if sys.stdout.isatty() or sys.stderr.isatty():
        return True
    return bool(env.get("TERM") or env.get("TERM_PROGRAM"))


def ring_bell(count: int, interval: float) -> None:
    count = max(1, count)
    interval = max(0.0, interval)
    for idx in range(count):
        sys.stdout.write("\a")
        sys.stdout.flush()
        if idx + 1 < count:
            time.sleep(interval)


def escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def notify_darwin(title: str, message: str) -> bool:
    script = (
        f'display notification "{escape_applescript(message)}" '
        f'with title "{escape_applescript(title)}"'
    )
    result = subprocess.run(["osascript", "-e", script], check=False)
    return result.returncode == 0


def notify_linux(title: str, message: str) -> bool:
    if not shutil.which("notify-send"):
        return False
    result = subprocess.run(["notify-send", title, message], check=False)
    return result.returncode == 0


def notify_windows(title: str, message: str) -> bool:
    _ = (title, message)
    return False


def notify_system(title: str, message: str) -> bool:
    if sys.platform == "darwin":
        return notify_darwin(title, message)
    if sys.platform.startswith("linux"):
        return notify_linux(title, message)
    if sys.platform.startswith("win"):
        return notify_windows(title, message)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified notification helper")
    parser.add_argument("--title", default="Codex")
    parser.add_argument("--message", default="Task finished.")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "terminal", "gui", "vscode", "all"],
    )
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()

    env = dict(os.environ)
    in_terminal = is_terminal_env(env)
    in_vscode = is_vscode_env(env)

    if args.mode == "auto":
        want_bell = in_terminal
        want_system = True
    elif args.mode == "terminal":
        want_bell = True
        want_system = False
    elif args.mode == "gui":
        want_bell = False
        want_system = True
    elif args.mode == "vscode":
        want_system = True
        want_bell = in_terminal or in_vscode
    else:  # all
        want_system = True
        want_bell = True

    system_ok = None
    if want_system:
        system_ok = notify_system(args.title, args.message)

    if want_bell:
        ring_bell(args.count, args.interval)

    if not want_system and not want_bell:
        sys.stderr.write("notify: no channels selected\n")
        return 1

    if want_system and not want_bell and not system_ok:
        sys.stderr.write("notify: system notification not available\n")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
