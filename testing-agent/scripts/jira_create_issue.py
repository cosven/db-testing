#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Iterable, Optional

import click
import requests
from requests.auth import HTTPBasicAuth


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


def resolve_value(value: Optional[str], env_key: str, required: bool = False) -> str:
    resolved = value or os.getenv(env_key, "")
    if required and not resolved:
        raise click.UsageError(f"Missing required value for {env_key}.")
    return resolved


def read_description(text: Optional[str], file_path: Optional[Path]) -> str:
    if text and file_path:
        raise click.UsageError("Provide either --description or --description-file, not both.")
    if file_path:
        return file_path.read_text(encoding="utf-8").strip()
    if text:
        return text
    raise click.UsageError("Missing description. Use --description or --description-file.")


def build_payload(
    project_key: str,
    issue_type: str,
    summary: str,
    description: str,
    labels: Iterable[str],
    components: Iterable[str],
    assignee: Optional[str],
    priority: Optional[str],
) -> dict:
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": issue_type},
    }
    label_list = [label for label in labels if label]
    if label_list:
        fields["labels"] = label_list
    component_list = [component for component in components if component]
    if component_list:
        fields["components"] = [{"name": name} for name in component_list]
    if assignee:
        fields["assignee"] = {"name": assignee}
    if priority:
        fields["priority"] = {"name": priority}
    return {"fields": fields}


@click.command(help="Create a Jira issue using REST API v2")
@click.option(
    "--env-file",
    default=".env",
    show_default=True,
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    help="Env file to load for Jira credentials",
)
@click.option("--jira-url", help="Jira base URL, default from JIRA_URL")
@click.option("--jira-user", help="Jira username/email, default from JIRA_USER")
@click.option("--jira-token", help="Jira API token, default from JIRA_TOKEN")
@click.option(
    "--auth",
    type=click.Choice(["bearer", "basic"]),
    default="bearer",
    show_default=True,
    help="Authentication method to use with the token",
)
@click.option("--project-key", help="Project key, default from JIRA_PROJECT")
@click.option(
    "--issue-type",
    default=None,
    help="Issue type, default from JIRA_ISSUE_TYPE or Bug",
)
@click.option("--summary", required=True, help="Issue summary")
@click.option("--description", help="Issue description")
@click.option(
    "--description-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Read description from file",
)
@click.option("--label", "labels", multiple=True, help="Add a label (repeatable)")
@click.option("--component", "components", multiple=True, help="Add a component (repeatable)")
@click.option("--assignee", help="Assignee username (optional)")
@click.option("--priority", help="Priority name (optional)")
@click.option("--print-payload", is_flag=True, help="Print request payload")
@click.option("--dry-run", is_flag=True, help="Only print payload, do not create issue")
def main(
    env_file: Path,
    jira_url: Optional[str],
    jira_user: Optional[str],
    jira_token: Optional[str],
    auth: str,
    project_key: Optional[str],
    issue_type: Optional[str],
    summary: str,
    description: Optional[str],
    description_file: Optional[Path],
    labels: Iterable[str],
    components: Iterable[str],
    assignee: Optional[str],
    priority: Optional[str],
    print_payload: bool,
    dry_run: bool,
) -> None:
    load_env_file(env_file)
    jira_url = resolve_value(jira_url, "JIRA_URL", required=True).rstrip("/")
    jira_token = resolve_value(jira_token, "JIRA_TOKEN", required=True)
    jira_user = resolve_value(jira_user, "JIRA_USER") if auth == "basic" else ""
    project_key = resolve_value(project_key, "JIRA_PROJECT", required=True)
    issue_type = issue_type or os.getenv("JIRA_ISSUE_TYPE", "Bug")
    description_text = read_description(description, description_file)

    payload = build_payload(
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description=description_text,
        labels=labels,
        components=components,
        assignee=assignee,
        priority=priority,
    )

    if print_payload or dry_run:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        if dry_run:
            return

    headers = {"Content-Type": "application/json"}
    request_auth = None
    if auth == "bearer":
        headers["Authorization"] = f"Bearer {jira_token}"
    else:
        if not jira_user:
            raise click.UsageError("Basic auth requires --jira-user or JIRA_USER.")
        request_auth = HTTPBasicAuth(jira_user, jira_token)

    url = f"{jira_url}/rest/api/2/issue"
    resp = requests.post(url, headers=headers, auth=request_auth, json=payload, timeout=20)
    if resp.status_code >= 400:
        click.echo(f"Request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)
    data = resp.json()
    key = data.get("key")
    self_url = data.get("self")
    if key:
        click.echo(f"key={key}")
    if self_url:
        click.echo(f"self={self_url}")


if __name__ == "__main__":
    main()
