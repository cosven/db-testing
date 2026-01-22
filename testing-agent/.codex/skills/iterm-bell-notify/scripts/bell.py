#!/usr/bin/env python3
import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger iTerm2 bell notifications")
    parser.add_argument("--count", type=int, default=3, help="Number of bells to send")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds to sleep between bells",
    )
    args = parser.parse_args()

    if args.count <= 0:
        return 0

    for i in range(args.count):
        sys.stdout.write("\a")
        sys.stdout.flush()
        if i != args.count - 1 and args.interval > 0:
            time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
