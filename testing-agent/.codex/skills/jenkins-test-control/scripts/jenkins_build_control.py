#!/usr/bin/env python3
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import quote

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


def build_job_path(job: str) -> str:
    parts = [part for part in job.strip("/").split("/") if part]
    if not parts:
        raise click.UsageError("Job name is empty.")
    return "/".join(f"job/{quote(part, safe='')}" for part in parts)


def normalize_param_value(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def extract_parameters(actions: Iterable[dict]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for action in actions or []:
        for param in action.get("parameters", []) or []:
            name = param.get("name")
            if not name:
                continue
            value = normalize_param_value(param.get("value"))
            if value is None:
                continue
            params[name] = value
    return params


def parse_param_overrides(items: Iterable[str]) -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise click.UsageError(f"Invalid --param value: {item}. Use KEY=VALUE.")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise click.UsageError(f"Invalid --param value: {item}.")
        overrides[key] = value
    return overrides


def parse_queue_id(queue_id: Optional[int], queue_url: Optional[str]) -> Optional[int]:
    if queue_id:
        return queue_id
    if not queue_url:
        return None
    match = re.search(r"/queue/item/(\d+)", queue_url)
    if not match:
        return None
    return int(match.group(1))


def get_crumb(base_url: str, auth: HTTPBasicAuth, timeout: int) -> Dict[str, str]:
    url = f"{base_url}/crumbIssuer/api/json"
    try:
        resp = requests.get(url, auth=auth, timeout=timeout)
    except requests.RequestException as exc:
        click.echo(f"Crumb issuer request failed: {exc}", err=True)
        return {}
    if resp.status_code >= 400:
        return {}
    data = resp.json()
    crumb = data.get("crumb")
    field = data.get("crumbRequestField")
    if crumb and field:
        return {field: crumb}
    return {}


def fetch_build_info(
    base_url: str,
    job_path: str,
    build: int,
    auth: HTTPBasicAuth,
    timeout: int,
) -> Tuple[bool, Dict[str, str]]:
    url = f"{base_url}/{job_path}/{build}/api/json?tree=building,actions[parameters[name,value]]"
    resp = requests.get(url, auth=auth, timeout=timeout)
    if resp.status_code >= 400:
        click.echo(f"Request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)
    data = resp.json()
    building = bool(data.get("building", False))
    params = extract_parameters(data.get("actions", []))
    return building, params


def fetch_build_status(
    base_url: str,
    job_path: str,
    build: int,
    auth: HTTPBasicAuth,
    timeout: int,
) -> dict:
    url = (
        f"{base_url}/{job_path}/{build}/api/json"
        "?tree=building,result,number,url,timestamp,duration,estimatedDuration"
    )
    resp = requests.get(url, auth=auth, timeout=timeout)
    if resp.status_code >= 400:
        click.echo(f"Request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)
    return resp.json()


def fetch_latest_build_status(
    base_url: str,
    job_path: str,
    auth: HTTPBasicAuth,
    timeout: int,
) -> Optional[dict]:
    url = (
        f"{base_url}/{job_path}/api/json"
        "?tree=lastBuild[number,url,building,result,timestamp,duration,estimatedDuration]"
    )
    resp = requests.get(url, auth=auth, timeout=timeout)
    if resp.status_code >= 400:
        click.echo(f"Request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)
    data = resp.json()
    return data.get("lastBuild")


def fetch_queue_item(
    base_url: str,
    queue_id: int,
    auth: HTTPBasicAuth,
    timeout: int,
    allow_not_found: bool = False,
) -> Optional[dict]:
    url = f"{base_url}/queue/item/{queue_id}/api/json"
    resp = requests.get(url, auth=auth, timeout=timeout)
    if resp.status_code == 404 and allow_not_found:
        return None
    if resp.status_code >= 400:
        click.echo(f"Queue request failed: {resp.status_code}", err=True)
        click.echo(resp.text, err=True)
        raise SystemExit(1)
    return resp.json()


def post_request(
    url: str,
    auth: HTTPBasicAuth,
    headers: Dict[str, str],
    timeout: int,
    data: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> requests.Response:
    if dry_run:
        click.echo(f"dry-run POST {url}")
        if data:
            click.echo(f"dry-run params: {sorted(data.keys())}")
        return requests.Response()
    resp = requests.post(url, auth=auth, headers=headers, data=data, timeout=timeout)
    return resp


def print_queue_location(resp: requests.Response) -> Optional[int]:
    if not resp:
        return None
    location = resp.headers.get("Location") or resp.headers.get("location")
    if location:
        click.echo(f"queue={location}")
        queue_id = parse_queue_id(None, location)
        if queue_id:
            click.echo(f"queue_id={queue_id}")
            return queue_id
    return None


def print_queue_status(queue_data: dict) -> Tuple[Optional[int], Optional[str]]:
    click.echo(f"queue_cancelled={queue_data.get('cancelled')}")
    if queue_data.get("why"):
        click.echo(f"queue_why={queue_data.get('why')}")
    executable = queue_data.get("executable") or {}
    build_number = executable.get("number")
    build_url = executable.get("url")
    if build_number is not None:
        click.echo("queue_executable=true")
        click.echo(f"queue_build_number={build_number}")
    if build_url:
        click.echo(f"queue_build_url={build_url}")
    if build_number is None:
        click.echo("queue_executable=false")
    return build_number, build_url


def print_build_status(status: dict) -> None:
    click.echo(f"build_number={status.get('number')}")
    click.echo(f"building={status.get('building')}")
    click.echo(f"result={status.get('result')}")
    if status.get("url"):
        click.echo(f"url={status.get('url')}")
    start_ms = int(status.get("timestamp") or 0)
    if start_ms:
        now_ms = int(time.time() * 1000)
        elapsed_ms = max(0, now_ms - start_ms)
        start_time = datetime.fromtimestamp(start_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"start_time={start_time}")
        click.echo(f"elapsed_seconds={elapsed_ms // 1000}")
    if status.get("estimatedDuration") is not None:
        click.echo(f"estimated_duration_seconds={int(status['estimatedDuration']) // 1000}")
    if status.get("duration") is not None:
        click.echo(f"duration_seconds={int(status['duration']) // 1000}")


def wait_for_queue_executable(
    base_url: str,
    queue_id: int,
    auth: HTTPBasicAuth,
    timeout: int,
    wait_seconds: int,
    poll_interval: int = 3,
) -> Optional[dict]:
    if wait_seconds <= 0:
        return fetch_queue_item(base_url, queue_id, auth, timeout)
    deadline = time.time() + wait_seconds
    last_data: Optional[dict] = None
    while True:
        remaining = deadline - time.time()
        if remaining < 0:
            break
        data = fetch_queue_item(base_url, queue_id, auth, timeout, allow_not_found=True)
        if data is None:
            return None
        last_data = data
        executable = data.get("executable") or {}
        if executable.get("number") is not None or data.get("cancelled"):
            return data
        if remaining <= 0:
            break
        time.sleep(min(poll_interval, remaining))
    return last_data


def wait_for_build_completion(
    base_url: str,
    job_path: str,
    build: int,
    auth: HTTPBasicAuth,
    timeout: int,
    wait_timeout: int,
    poll_interval: int,
) -> Tuple[dict, bool]:
    deadline = time.time() + wait_timeout if wait_timeout > 0 else None
    last_status = fetch_build_status(base_url, job_path, build, auth, timeout)
    while True:
        if not last_status.get("building"):
            return last_status, False
        if deadline is not None and time.time() >= deadline:
            return last_status, True
        time.sleep(max(1, poll_interval))
        last_status = fetch_build_status(base_url, job_path, build, auth, timeout)
    return last_status, True


def format_testrun_line(
    job: str,
    build: Optional[int],
    building: Optional[bool],
    result: Optional[str],
    url: Optional[str],
    queue_id: Optional[int],
    queue_url: Optional[str],
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"time={timestamp}", f"job={job}"]
    if build is not None:
        parts.append(f"build={build}")
    if building is not None:
        parts.append(f"building={building}")
    if result:
        parts.append(f"result={result}")
    if url:
        parts.append(f"url={url}")
    if queue_id is not None:
        parts.append(f"queue_id={queue_id}")
    if queue_url:
        parts.append(f"queue_url={queue_url}")
    return f"- jenkins_build: {', '.join(parts)}"


def append_testrun_entry(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        is_empty = path.stat().st_size == 0
    except FileNotFoundError:
        is_empty = True
    with path.open("a", encoding="utf-8") as handle:
        if not is_empty:
            handle.write("\n")
        handle.write(f"{line.rstrip()}\n")


@click.command(help="Stop and rebuild Jenkins builds using the REST API")
@click.option(
    "--env-file",
    default=".env",
    show_default=True,
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    help="Env file to load for Jenkins settings",
)
@click.option("--jenkins-url", help="Jenkins base URL, default from JENKINS_URL")
@click.option("--jenkins-user", help="Jenkins username, default from JENKINS_USER")
@click.option("--jenkins-token", help="Jenkins API token, default from JENKINS_TOKEN")
@click.option("--job", required=True, help="Jenkins job name, supports folders (a/b/job)")
@click.option("--build", type=int, help="Build number to control")
@click.option("--stop", "do_stop", is_flag=True, help="Stop the specified build")
@click.option("--rebuild", "do_rebuild", is_flag=True, help="Rebuild the specified build")
@click.option("--status", "show_status", is_flag=True, help="Show build status")
@click.option("--latest", "show_latest", is_flag=True, help="Show latest build status")
@click.option("--queue-id", type=int, help="Queue item id to query")
@click.option("--queue-url", help="Queue item URL to query")
@click.option(
    "--queue-wait-seconds",
    type=int,
    default=None,
    help="Wait for queue item to get executable build (default: 30s with --rebuild, 0 otherwise)",
)
@click.option("--wait", "wait_for_completion", is_flag=True, help="Wait for build completion")
@click.option(
    "--wait-timeout",
    default=0,
    show_default=True,
    help="Max seconds to wait; 0 means no limit",
)
@click.option(
    "--wait-interval",
    default=10,
    show_default=True,
    help="Polling interval seconds while waiting",
)
@click.option(
    "--testrun-file",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Append build info to testrun README",
)
@click.option("--param", "param_overrides", multiple=True, help="Override build param KEY=VALUE")
@click.option("--timeout", default=20, show_default=True, help="HTTP timeout seconds")
@click.option("--dry-run", is_flag=True, help="Only print actions, do not call Jenkins")
def main(
    env_file: Path,
    jenkins_url: Optional[str],
    jenkins_user: Optional[str],
    jenkins_token: Optional[str],
    job: str,
    build: Optional[int],
    do_stop: bool,
    do_rebuild: bool,
    show_status: bool,
    show_latest: bool,
    queue_id: Optional[int],
    queue_url: Optional[str],
    queue_wait_seconds: Optional[int],
    wait_for_completion: bool,
    wait_timeout: int,
    wait_interval: int,
    testrun_file: Optional[Path],
    param_overrides: Iterable[str],
    timeout: int,
    dry_run: bool,
) -> None:
    load_env_file(env_file)
    base_url = resolve_value(jenkins_url, "JENKINS_URL", required=True).rstrip("/")
    user = resolve_value(jenkins_user, "JENKINS_USER", required=True)
    token = resolve_value(jenkins_token, "JENKINS_TOKEN", required=True)
    if not (do_stop or do_rebuild or show_status or show_latest or queue_id or queue_url or wait_for_completion):
        raise click.UsageError("Nothing to do. Use --stop/--rebuild/--status/--latest or queue options.")

    auth = HTTPBasicAuth(user, token)
    job_path = build_job_path(job)
    crumb_headers = get_crumb(base_url, auth, timeout)

    queue_wait_seconds = 30 if queue_wait_seconds is None and do_rebuild else (queue_wait_seconds or 0)
    queue_id = parse_queue_id(queue_id, queue_url)
    queue_build_number: Optional[int] = None
    queue_build_url: Optional[str] = None
    latest_status: Optional[dict] = None
    status_for_record: Optional[dict] = None
    record_queue_id: Optional[int] = queue_id
    record_queue_url: Optional[str] = queue_url
    if queue_id:
        if queue_wait_seconds:
            queue_data = wait_for_queue_executable(
                base_url, queue_id, auth, timeout, queue_wait_seconds
            )
            click.echo(f"queue_wait_seconds={queue_wait_seconds}")
        else:
            queue_data = fetch_queue_item(base_url, queue_id, auth, timeout)
        if queue_data is None:
            click.echo("queue_not_found=true")
        else:
            queue_build_number, queue_build_url = print_queue_status(queue_data)
            if queue_wait_seconds and queue_build_number is None:
                click.echo("queue_wait_timeout=true")
        if record_queue_url is None and record_queue_id is not None:
            record_queue_url = f"{base_url}/queue/item/{record_queue_id}/"

    if build is None and queue_build_number is not None:
        build = queue_build_number

    if (do_stop or do_rebuild or show_status) and build is None:
        raise click.UsageError("Missing --build for stop/rebuild/status.")

    if show_latest:
        latest_status = fetch_latest_build_status(base_url, job_path, auth, timeout)
        if latest_status:
            click.echo("latest_build=true")
            print_build_status(latest_status)
        else:
            click.echo("latest_build=false")

    if show_status and build is not None:
        status_for_record = fetch_build_status(base_url, job_path, build, auth, timeout)
        print_build_status(status_for_record)

    params: Dict[str, str] = {}
    building = False
    if do_stop or do_rebuild:
        building, params = fetch_build_info(base_url, job_path, build, auth, timeout)
        overrides = parse_param_overrides(param_overrides)
        params.update(overrides)
        click.echo(f"building={building}")
        click.echo(f"param_count={len(params)}")

    if do_stop:
        if not building:
            click.echo("skip stop: build is not running")
        else:
            stop_url = f"{base_url}/{job_path}/{build}/stop"
            resp = post_request(stop_url, auth, crumb_headers, timeout, dry_run=dry_run)
            if not dry_run:
                click.echo(f"stop_status={resp.status_code}")
                if resp.status_code >= 400:
                    click.echo(resp.text, err=True)
                    raise SystemExit(1)

    rebuild_queue_id: Optional[int] = None
    rebuild_queue_url: Optional[str] = None
    if do_rebuild:
        rebuild_url = f"{base_url}/{job_path}/{build}/rebuild"
        resp = post_request(rebuild_url, auth, crumb_headers, timeout, dry_run=dry_run)
        if dry_run:
            click.echo("dry-run rebuild requested")
            return
        if resp.status_code >= 400:
            build_url = (
                f"{base_url}/{job_path}/buildWithParameters" if params else f"{base_url}/{job_path}/build"
            )
            resp = post_request(build_url, auth, crumb_headers, timeout, data=params)
            click.echo("rebuild_fallback=buildWithParameters" if params else "rebuild_fallback=build")
        click.echo(f"rebuild_status={resp.status_code}")
        if resp.status_code >= 400:
            click.echo(resp.text, err=True)
            raise SystemExit(1)
        rebuild_queue_id = print_queue_location(resp)
        rebuild_queue_url = resp.headers.get("Location") or resp.headers.get("location")
        if rebuild_queue_id:
            record_queue_id = rebuild_queue_id
            record_queue_url = rebuild_queue_url or f"{base_url}/queue/item/{rebuild_queue_id}/"
        if rebuild_queue_id and queue_wait_seconds:
            queue_data = wait_for_queue_executable(
                base_url, rebuild_queue_id, auth, timeout, queue_wait_seconds
            )
            click.echo(f"queue_wait_seconds={queue_wait_seconds}")
            if queue_data is None:
                click.echo("queue_not_found=true")
            else:
                queue_build_number, queue_build_url = print_queue_status(queue_data)
                if queue_build_number is None:
                    click.echo("queue_wait_timeout=true")

    wait_build_number: Optional[int] = None
    if wait_for_completion:
        if queue_build_number is not None and do_rebuild:
            wait_build_number = queue_build_number
        elif build is not None:
            wait_build_number = build
        elif latest_status and latest_status.get("number") is not None:
            wait_build_number = int(latest_status["number"])
        else:
            raise click.UsageError("Missing build number for --wait.")
        wait_timeout = max(0, wait_timeout)
        wait_interval = max(1, wait_interval)
        status_for_record, timed_out = wait_for_build_completion(
            base_url, job_path, wait_build_number, auth, timeout, wait_timeout, wait_interval
        )
        click.echo("wait_timeout=true" if timed_out else "wait_done=true")
        print_build_status(status_for_record)

    if testrun_file:
        record_build = None
        record_url = None
        record_building = None
        record_result = None
        if status_for_record:
            record_build = status_for_record.get("number")
            record_url = status_for_record.get("url")
            record_building = status_for_record.get("building")
            record_result = status_for_record.get("result")
        elif latest_status:
            record_build = latest_status.get("number")
            record_url = latest_status.get("url")
            record_building = latest_status.get("building")
            record_result = latest_status.get("result")
        elif queue_build_number is not None:
            record_build = queue_build_number
            record_url = queue_build_url
        if any([record_build, record_url, record_queue_id, record_queue_url]):
            line = format_testrun_line(
                job=job,
                build=record_build,
                building=record_building,
                result=record_result,
                url=record_url,
                queue_id=record_queue_id,
                queue_url=record_queue_url,
            )
            append_testrun_entry(testrun_file, line)


if __name__ == "__main__":
    main()
