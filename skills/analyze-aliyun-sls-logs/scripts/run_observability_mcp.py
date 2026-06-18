#!/usr/bin/env python3
"""Launch Alibaba Cloud Observability MCP in stdio mode for plugin installs."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


REPO_WEB_URL = "https://github.com/aliyun/alibabacloud-observability-mcp-server"
REPO_URL = f"{REPO_WEB_URL}.git"
BINARY_NAME = "alibabacloud-observability-mcp-server"
ENV_KEYS = (
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_SECURITY_TOKEN",
    "ALIBABA_CLOUD_REGION",
    "ALIBABA_CLOUD_WORKSPACE",
)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def install_dir() -> Path:
    return Path(os.environ.get("ALIBABA_CLOUD_OBSERVABILITY_MCP_HOME", "~/alibabacloud-observability-mcp-server")).expanduser()


def binary_path(root: Path) -> Path:
    return root / "bin" / BINARY_NAME


def run(cmd: list[str], cwd: Path | None = None) -> None:
    log("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True, stdout=sys.stderr, stderr=sys.stderr)


def release_asset_url() -> str | None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name = {"darwin": "darwin", "linux": "linux", "windows": "windows"}.get(system)
    arch = {
        "arm64": "arm64",
        "aarch64": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
    }.get(machine)
    if not os_name or not arch:
        return None
    suffix = ".zip" if os_name == "windows" else ".tar.gz"
    return f"{REPO_WEB_URL}/releases/latest/download/{BINARY_NAME}-{os_name}-{arch}{suffix}"


def safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = []
    for member in archive.getmembers():
        target = Path(member.name)
        if target.is_absolute() or ".." in target.parts:
            raise RuntimeError(f"unsafe archive member: {member.name}")
        members.append(member)
    return members


def install_release(root: Path) -> bool:
    url = release_asset_url()
    if not url:
        return False

    log(f"Downloading {url}")
    try:
        with tempfile.TemporaryDirectory(prefix="obs-mcp-release-") as temp_dir:
            temp = Path(temp_dir)
            archive_path = temp / "release.tar.gz"
            with urllib.request.urlopen(url, timeout=60) as response:
                archive_path.write_bytes(response.read())
            with tarfile.open(archive_path, "r:gz") as archive:
                archive.extractall(temp / "extract", members=safe_members(archive))

            extracted_binary = next((p for p in (temp / "extract").rglob(BINARY_NAME) if p.is_file()), None)
            extracted_config = next((p for p in (temp / "extract").rglob("config.yaml") if p.is_file()), None)
            if not extracted_binary:
                raise RuntimeError("release archive did not contain the MCP binary")

            (root / "bin").mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted_binary, binary_path(root))
            binary_path(root).chmod(0o755)
            if extracted_config and not (root / "config.yaml").exists():
                shutil.copy2(extracted_config, root / "config.yaml")
            return True
    except (OSError, RuntimeError, tarfile.TarError, urllib.error.URLError) as exc:
        log(f"Release download failed: {exc}")
        return False


def build_from_source(root: Path) -> None:
    if root.exists() and not (root / ".git").exists() and not any(root.iterdir()):
        run(["git", "clone", REPO_URL, str(root)])
    elif not root.exists():
        if not shutil.which("git"):
            raise SystemExit("git is required to install alibabacloud-observability-mcp-server")
        run(["git", "clone", REPO_URL, str(root)])
    elif not (root / ".git").exists():
        raise SystemExit(f"{root} exists but is not the expected git checkout")

    if not shutil.which("go"):
        raise SystemExit("Go >= 1.23 is required to build alibabacloud-observability-mcp-server")
    if not shutil.which("make"):
        raise SystemExit("make is required to build alibabacloud-observability-mcp-server")

    run(["make", "build"], cwd=root)
    binary_path(root).chmod(binary_path(root).stat().st_mode | 0o111)


def ensure_server(root: Path) -> None:
    binary = binary_path(root)
    if binary.exists():
        return

    root.mkdir(parents=True, exist_ok=True)
    if install_release(root):
        return
    build_from_source(root)


def load_env_file(root: Path) -> None:
    env_file = root / ".env"
    if not env_file.exists():
        source = root / ".env.example"
        if source.exists():
            shutil.copy2(source, env_file)
            log(f"Created {env_file}; fill credentials there or set ALIBABA_CLOUD_* environment variables.")
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in ENV_KEYS and value and key not in os.environ:
            os.environ[key] = value


def check(root: Path) -> int:
    ensure_server(root)
    load_env_file(root)
    missing = [key for key in ("ALIBABA_CLOUD_ACCESS_KEY_ID", "ALIBABA_CLOUD_ACCESS_KEY_SECRET") if not os.environ.get(key)]
    log(f"server={binary_path(root)}")
    log("credentials=" + ("missing:" + ",".join(missing) if missing else "present"))
    return 1 if missing else 0


def main() -> int:
    root = install_dir()
    if "--check" in sys.argv:
        return check(root)

    ensure_server(root)
    load_env_file(root)
    config = root / "config.yaml"
    if not config.exists():
        raise SystemExit(f"missing config file: {config}")

    binary = binary_path(root)
    argv = [str(binary), "start", "--stdio", "--config", str(config)]
    os.execvpe(str(binary), argv, os.environ)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
