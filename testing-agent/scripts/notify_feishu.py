#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Optional

import click
import requests
from requests import Response


DEFAULT_FEISHU_NOTIFY_ENDPOINT = "http://notify.example.com/api/v1/feishu-messages"


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_value(value: Optional[str], env_key: str, default: Optional[str] = None) -> str:
    if value:
        return value
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    return default or ""


def read_card(
    card_json: Optional[str],
    card_file: Optional[Path],
    title: Optional[str],
    markdown: Optional[str],
) -> dict:
    if card_json or card_file:
        if title or markdown:
            raise click.UsageError(
                "Provide either card JSON (--card-json/--card-file) or --title/--markdown."
            )
        if card_file:
            return json.loads(card_file.read_text(encoding="utf-8"))
        return json.loads(card_json)
    if not title or not markdown:
        raise click.UsageError(
            "Missing card content. Use --card-json/--card-file or --title with --markdown."
        )
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": title}},
        "elements": [{"tag": "markdown", "content": markdown}],
    }


def ensure_ok(resp: Response) -> None:
    if resp.status_code >= 400:
        click.echo(f"Request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)


def send_webhook(webhook: str, card: dict) -> str:
    body = {"msg_type": "interactive", "card": card}
    resp = requests.post(webhook, json=body, timeout=10)
    ensure_ok(resp)
    return resp.text


def send_personal(notify_endpoint: str, github_name: str, card: dict) -> str:
    params = {"msg_type": "interactive", "github_name": github_name}
    resp = requests.post(notify_endpoint, params=params, json=card, timeout=10)
    ensure_ok(resp)
    return resp.text


@click.command(help="Send Feishu notification with an interactive card")
@click.option(
    "--env-file",
    default=".env",
    show_default=True,
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    help="Env file to load for notify settings",
)
@click.option(
    "--notify-endpoint",
    help="Feishu notify endpoint, default from FEISHU_NOTIFY_ENDPOINT",
)
@click.option("--webhook", help="Feishu webhook URL (https://...)")
@click.option("--name", help="Github name for personal notify")
@click.option("--card-json", help="Card JSON string")
@click.option(
    "--card-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Card JSON file",
)
@click.option("--title", help="Simple card title")
@click.option("--markdown", help="Simple card markdown content")
@click.option("--print-payload", is_flag=True, help="Print the card payload")
@click.option("--dry-run", is_flag=True, help="Only print payload, do not send")
def main(
    env_file: Path,
    notify_endpoint: Optional[str],
    webhook: Optional[str],
    name: Optional[str],
    card_json: Optional[str],
    card_file: Optional[Path],
    title: Optional[str],
    markdown: Optional[str],
    print_payload: bool,
    dry_run: bool,
) -> None:
    load_env_file(env_file)
    notify_endpoint = resolve_value(
        notify_endpoint, "FEISHU_NOTIFY_ENDPOINT", DEFAULT_FEISHU_NOTIFY_ENDPOINT
    )
    webhook = resolve_value(webhook, "FEISHU_WEBHOOK")
    name = resolve_value(name, "FEISHU_GITHUB_NAME")

    if webhook and name:
        raise click.UsageError("Provide either --webhook or --name, not both.")
    if not webhook and not name:
        raise click.UsageError("Missing target. Use --webhook/--name or env values.")

    card = read_card(card_json, card_file, title, markdown)
    if print_payload or dry_run:
        click.echo(json.dumps(card, ensure_ascii=False, indent=2))
        if dry_run:
            return

    if webhook:
        resp_text = send_webhook(webhook, card)
    else:
        resp_text = send_personal(notify_endpoint, name, card)
    click.echo(resp_text)


if __name__ == "__main__":
    main()
