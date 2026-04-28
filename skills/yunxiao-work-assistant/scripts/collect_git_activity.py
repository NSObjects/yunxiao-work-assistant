#!/usr/bin/env python3
"""收集用于工作汇报的 Git 提交，不修改仓库。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


REF_PATTERNS = [
    re.compile(r"(?:workitem|workItemId|work_item_id)[=/:-]([A-Za-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"(?:YUNXIAO|REQ|TASK|BUG)-\d+", re.IGNORECASE),
    re.compile(r"#(\d{4,})"),
]


@dataclass
class CommitActivity:
    repo: str
    hash: str
    short_hash: str
    date: str
    author_name: str
    author_email: str
    subject: str
    additions: int
    deletions: int
    files: list[str]
    work_item_refs: list[str]


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def parse_numstat(output: str) -> tuple[int, int, list[str]]:
    additions = 0
    deletions = 0
    files: list[str] = []

    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        add_raw, del_raw, path = parts[0], parts[1], parts[2]
        if add_raw.isdigit():
            additions += int(add_raw)
        if del_raw.isdigit():
            deletions += int(del_raw)
        files.append(path)

    return additions, deletions, files


def extract_refs(text: str) -> list[str]:
    refs: set[str] = set()
    for pattern in REF_PATTERNS:
        for match in pattern.finditer(text):
            refs.add(match.group(1) if match.groups() else match.group(0))
    return sorted(refs)


def collect_repo(repo: Path, since: str, until: str, author: str | None, max_count: int | None) -> list[CommitActivity]:
    if not repo.exists():
        raise RuntimeError(f"repo not found: {repo}")

    log_args = ["log", f"--since={since}", f"--until={until}", "--format=%H"]
    if author:
        log_args.append(f"--author={author}")
    if max_count:
        log_args.append(f"--max-count={max_count}")

    hashes = [line.strip() for line in run_git(repo, log_args).splitlines() if line.strip()]
    commits: list[CommitActivity] = []

    for commit_hash in hashes:
        meta = run_git(
            repo,
            [
                "show",
                "-s",
                "--format=%H%n%h%n%aI%n%an%n%ae%n%s%n%B",
                commit_hash,
            ],
        ).splitlines()
        if len(meta) < 6:
            continue

        full_hash, short_hash, date, author_name, author_email, subject = meta[:6]
        body = "\n".join(meta[6:])
        numstat = run_git(repo, ["show", "--format=", "--numstat", commit_hash])
        additions, deletions, files = parse_numstat(numstat)
        refs = extract_refs(subject + "\n" + body)

        commits.append(
            CommitActivity(
                repo=str(repo.resolve()),
                hash=full_hash,
                short_hash=short_hash,
                date=date,
                author_name=author_name,
                author_email=author_email,
                subject=subject,
                additions=additions,
                deletions=deletions,
                files=files,
                work_item_refs=refs,
            )
        )

    return commits


def render_markdown(commits: Iterable[CommitActivity]) -> str:
    lines = ["# Git 提交活动", ""]
    for commit in commits:
        refs = ", ".join(commit.work_item_refs) if commit.work_item_refs else "none"
        files = ", ".join(commit.files[:8])
        if len(commit.files) > 8:
            files += f", ... (+{len(commit.files) - 8})"

        lines.extend(
            [
                f"## `{commit.short_hash}` {commit.subject}",
                "",
                f"- repo: `{commit.repo}`",
                f"- date: {commit.date}",
                f"- author: {commit.author_name} <{commit.author_email}>",
                f"- stats: +{commit.additions} -{commit.deletions}, {len(commit.files)} files",
                f"- work_item_refs: {refs}",
                f"- files: {files or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="收集云效工作汇报所需的 Git 提交。")
    parser.add_argument("--repo", action="append", default=None, help="Git 仓库路径。多个仓库可重复传入。")
    parser.add_argument("--since", required=True, help="git 可识别的开始日期或时间，例如 2026-04-20。")
    parser.add_argument("--until", required=True, help="git 可识别的结束日期或时间，例如 2026-04-26 23:59:59。")
    parser.add_argument("--author", help="可选的 Git 作者姓名或邮箱过滤条件。")
    parser.add_argument("--max-count", type=int, help="可选的每个仓库最大提交数量。")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    repos = [Path(repo).expanduser() for repo in (args.repo or ["."])]
    activities: list[CommitActivity] = []

    try:
        for repo in repos:
            activities.extend(collect_repo(repo, args.since, args.until, args.author, args.max_count))
    except RuntimeError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps([asdict(activity) for activity in activities], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(activities), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
