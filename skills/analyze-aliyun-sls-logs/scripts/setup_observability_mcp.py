#!/usr/bin/env python3
"""Install and configure Alibaba Cloud Observability MCP for Codex."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_URL = "https://github.com/aliyun/alibabacloud-observability-mcp-server.git"
SERVER_NAME = "alibaba_cloud_observability"
BINARY_NAME = "alibabacloud-observability-mcp-server"
MCP_ENV_KEYS = [
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_SECURITY_TOKEN",
    "ALIBABA_CLOUD_REGION",
    "ALIBABA_CLOUD_WORKSPACE",
]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


def binary_path(install_dir: Path) -> Path:
    return install_dir / "bin" / BINARY_NAME


def default_codex_config() -> str:
    return str(Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "config.toml")


def ensure_server(install_dir: Path, dry_run: bool) -> None:
    binary = binary_path(install_dir)
    if binary.exists():
        print(f"OK server binary: {binary}")
        return

    if not install_dir.exists():
        if dry_run:
            print(f"DRY would clone {REPO_URL} into {install_dir}")
        else:
            run(["git", "clone", REPO_URL, str(install_dir)])
    elif not (install_dir / ".git").exists():
        raise SystemExit(f"Install directory exists but is not the expected git checkout: {install_dir}")

    if not shutil.which("go"):
        raise SystemExit("Go is required to build the MCP server. Install Go >= 1.23, then rerun this script.")
    if not shutil.which("make"):
        raise SystemExit("make is required to build the MCP server. Install make, then rerun this script.")

    if dry_run:
        print(f"DRY would build MCP server in {install_dir}")
        return

    run(["make", "build"], cwd=install_dir)
    binary.chmod(binary.stat().st_mode | 0o111)
    print(f"OK built server binary: {binary}")


def read_env_lines(env_file: Path) -> list[str]:
    if not env_file.exists():
        return []
    return env_file.read_text(encoding="utf-8").splitlines()


def upsert_env(lines: list[str], key: str, value: str | None) -> list[str]:
    if not value:
        return lines
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    replacement = f"{key}={value}"
    for idx, line in enumerate(lines):
        if pattern.match(line):
            lines[idx] = replacement
            return lines
    lines.append(replacement)
    return lines


def ensure_env(install_dir: Path, region: str | None, workspace: str | None, dry_run: bool) -> None:
    env_file = install_dir / ".env"
    if not env_file.exists():
        source = install_dir / ".env.example"
        if dry_run:
            print(f"DRY would create {env_file}")
        elif source.exists():
            shutil.copy2(source, env_file)
        else:
            env_file.write_text(
                "ALIBABA_CLOUD_ACCESS_KEY_ID=\n"
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET=\n"
                "ALIBABA_CLOUD_REGION=cn-hangzhou\n"
                "ALIBABA_CLOUD_WORKSPACE=\n",
                encoding="utf-8",
            )

    lines = read_env_lines(env_file)
    original = list(lines)
    lines = upsert_env(lines, "ALIBABA_CLOUD_REGION", region)
    lines = upsert_env(lines, "ALIBABA_CLOUD_WORKSPACE", workspace)
    if lines != original:
        if dry_run:
            print(f"DRY would update region/workspace in {env_file}")
        else:
            env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"OK updated {env_file}")
    else:
        print(f"OK env file: {env_file}")

    env_text = "\n".join(lines)
    has_key = bool(os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")) or bool(
        re.search(r"^ALIBABA_CLOUD_ACCESS_KEY_ID=.+", env_text, re.MULTILINE)
    )
    has_secret = bool(os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")) or bool(
        re.search(r"^ALIBABA_CLOUD_ACCESS_KEY_SECRET=.+", env_text, re.MULTILINE)
    )
    if not (has_key and has_secret):
        print(f"WARN credentials not found. Fill {env_file} or export Alibaba Cloud credential env vars.")


def backup(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = path.with_suffix(path.suffix + f".backup.{stamp}")
    shutil.copy2(path, dest)
    return dest


def parse_env_file(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read_env_lines(env_file):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in MCP_ENV_KEYS and value:
            values[key] = value
    return values


def load_mcp_env(
    install_dir: Path,
    env_source: str,
    region: str | None,
    workspace: str | None,
) -> dict[str, str]:
    values: dict[str, str] = {}
    if env_source in {"auto", "env-file"}:
        values.update(parse_env_file(install_dir / ".env"))
    if env_source in {"auto", "process-env"}:
        for key in MCP_ENV_KEYS:
            if os.environ.get(key):
                values[key] = os.environ[key]
    if region:
        values["ALIBABA_CLOUD_REGION"] = region
    if workspace:
        values["ALIBABA_CLOUD_WORKSPACE"] = workspace
    return {key: values[key] for key in MCP_ENV_KEYS if values.get(key)}


def toml_quote(value: str) -> str:
    return json.dumps(value)


def build_mcp_block(install_dir: Path, mode: str, url: str, env_values: dict[str, str]) -> str:
    if mode == "http":
        return f"[mcp_servers.{SERVER_NAME}]\nurl = {toml_quote(url)}"

    binary = binary_path(install_dir)
    config = install_dir / "config.yaml"
    args = ["start", "--stdio", "--config", str(config)]
    lines = [
        f"[mcp_servers.{SERVER_NAME}]",
        f"command = {toml_quote(str(binary))}",
        "args = [" + ", ".join(toml_quote(arg) for arg in args) + "]",
    ]
    if env_values:
        lines.append("")
        lines.append(f"[mcp_servers.{SERVER_NAME}.env]")
        for key, value in env_values.items():
            lines.append(f"{key} = {toml_quote(value)}")
    return "\n".join(lines)


def remove_existing_mcp_blocks(text: str) -> str:
    for table in (f"mcp_servers.{SERVER_NAME}.env", f"mcp_servers.{SERVER_NAME}"):
        text = re.sub(rf"(?ms)^\[{re.escape(table)}\]\n.*?(?=^\[|\Z)", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).rstrip()


def table_block(text: str, table: str) -> str:
    match = re.search(rf"(?ms)^\[{re.escape(table)}\]\n.*?(?=^\[|\Z)", text)
    return match.group(0).strip() if match else ""


def existing_mcp_block(text: str) -> str:
    blocks = [
        table_block(text, f"mcp_servers.{SERVER_NAME}"),
        table_block(text, f"mcp_servers.{SERVER_NAME}.env"),
    ]
    return "\n\n".join(block for block in blocks if block)


def ensure_codex_config(
    config_path: Path,
    install_dir: Path,
    mode: str,
    url: str,
    env_values: dict[str, str],
    dry_run: bool,
) -> None:
    block = build_mcp_block(install_dir, mode, url, env_values)
    if not config_path.exists():
        new_text = f"[mcp_servers]\n\n{block}\n"
        if dry_run:
            print(f"DRY would create {config_path}")
        else:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(new_text, encoding="utf-8")
            config_path.chmod(0o600)
            print(f"OK created {config_path}")
        return

    text = config_path.read_text(encoding="utf-8")
    if existing_mcp_block(text) == block:
        print(f"OK Codex MCP config already has {SERVER_NAME} in {mode} mode")
        return

    new_text = remove_existing_mcp_blocks(text)
    if "[mcp_servers]" not in new_text:
        new_text = "[mcp_servers]\n\n" + new_text.lstrip()
    new_text = new_text.rstrip() + "\n\n" + block + "\n"

    if new_text == text:
        print(f"OK Codex MCP config already has {SERVER_NAME} in {mode} mode")
        return

    if dry_run:
        print(f"DRY would update {config_path} with {SERVER_NAME} in {mode} mode")
        return

    backup_path = backup(config_path)
    config_path.write_text(new_text, encoding="utf-8")
    print(f"OK updated {config_path}; backup: {backup_path}")


def health_url_from_mcp_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/health", "", "", ""))


def health_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def start_server(install_dir: Path, mcp_url: str, dry_run: bool) -> None:
    health_url = health_url_from_mcp_url(mcp_url)
    if health_ok(health_url):
        print(f"OK MCP health: {health_url}")
        return

    binary = binary_path(install_dir)
    config = install_dir / "config.yaml"
    if not binary.exists():
        raise SystemExit(f"Missing server binary: {binary}")
    if not config.exists():
        raise SystemExit(f"Missing config.yaml: {config}")

    if dry_run:
        print(f"DRY would start {binary} start --config {config}")
        return

    logs_dir = install_dir / "logs"
    run_dir = install_dir / "run"
    logs_dir.mkdir(exist_ok=True)
    run_dir.mkdir(exist_ok=True)
    stdout = open(logs_dir / "server-streamable-http.log", "ab")
    stderr = open(logs_dir / "server-streamable-http.err.log", "ab")
    proc = subprocess.Popen(
        [str(binary), "start", "--config", str(config)],
        cwd=str(install_dir),
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
    )
    (run_dir / "server.pid").write_text(str(proc.pid), encoding="utf-8")

    for _ in range(20):
        if health_ok(health_url, timeout=1.0):
            print(f"OK started MCP server pid={proc.pid}; health: {health_url}")
            return
        time.sleep(0.5)

    raise SystemExit(f"Started pid={proc.pid}, but health check did not pass: {health_url}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-dir", default="~/alibabacloud-observability-mcp-server")
    parser.add_argument("--codex-config", default=default_codex_config())
    parser.add_argument("--mode", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--url", default="http://127.0.0.1:8180/streamhttp")
    parser.add_argument("--env-source", choices=["auto", "env-file", "process-env", "none"], default="auto")
    parser.add_argument("--region", help="Optional default Alibaba Cloud region to write into .env")
    parser.add_argument("--workspace", help="Optional default CMS workspace to write into .env")
    parser.add_argument("--start", action="store_true", help="Start the local HTTP MCP server when --mode http")
    parser.add_argument("--dry-run", action="store_true", help="Print intended changes without writing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    install_dir = expand(args.install_dir)
    codex_config = expand(args.codex_config)

    ensure_server(install_dir, args.dry_run)
    ensure_env(install_dir, args.region, args.workspace, args.dry_run)
    env_values = load_mcp_env(install_dir, args.env_source, args.region, args.workspace)
    ensure_codex_config(codex_config, install_dir, args.mode, args.url, env_values, args.dry_run)

    if args.mode == "stdio":
        if not env_values.get("ALIBABA_CLOUD_ACCESS_KEY_ID") or not env_values.get(
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        ):
            print("WARN Codex MCP env has no AccessKey ID/Secret. Fill .env or export env vars, then rerun.")
        if args.dry_run:
            print("DRY stdio mode would let Codex start the MCP server with configured env vars.")
        else:
            print("OK stdio mode configured. Codex will start the MCP server with configured env vars.")
    elif args.start:
        start_server(install_dir, args.url, args.dry_run)
    else:
        health_url = health_url_from_mcp_url(args.url)
        if health_ok(health_url):
            print(f"OK MCP health: {health_url}")
        else:
            print(f"WARN MCP server is not healthy at {health_url}. Rerun with --start to launch it.")

    print("DONE Alibaba Cloud Observability MCP setup check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
