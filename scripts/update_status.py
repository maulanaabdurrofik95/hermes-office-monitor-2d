#!/usr/bin/env python
"""hermes-update-status — auto-write per-agent status JSON, git commit + push.

Usage (Linux/macOS via python3 / Windows via `python`):
  python scripts/update_status.py --agent hermes --stage working \
      --task "Orchestrate workflow" --task "Monitor agents" \
      --note "Reviewing frontend PR."

Setenv / flags:
  --agent NAME     (required) one of: hermes, dev, frontend, security, design
                     Also accepts the long form: orchestrator, developer, etc.
  --stage NAME     (required) e.g. idle, working, in-review, blocked, done
  --task TEXT      (repeatable) append/replace task list by default (append)
  --no-task        (flag) clear the task list before applying --task
  --note TEXT      (optional) human-readable status note
  --repo PATH      (optional) override repo root (default: auto git rev-parse)
  --no-push        (flag) skip git push (still commit locally)

Exit codes: 0 ok, 1 bad args, 2 git error, 3 json error
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, datetime
from pathlib import Path

AGENT_KEYS = {
    # canonical short name -> accepted aliases
    "hermes":  {"orchestrator", "hermes"},
    "dev":     {"dev", "developer", "backend", "dev-backend"},
    "frontend":{"frontend", "dev-frontend", "ui", "dev-frontend-monitor"},
    "security":{"security", "sec", "infosec", "security-monitor"},
    "design":  {"design", "uiux", "ux", "designer", "design-monitor"},
}

def resolve_agent(raw: str) -> str:
    r = raw.lower().strip()
    for canonical, aliases in AGENT_KEYS.items():
        if r in aliases or r == canonical:
            return canonical
    raise SystemExit(f"Error: unknown agent '{raw}'. "
                     f"Valid: {', '.join(AGENT_KEYS)} (or aliases).")

def repo_root(override: str | None) -> Path:
    if override:
        p = Path(override).resolve()
    else:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            raise SystemExit("Error: not inside a git repo and --repo not given.")
        p = Path(res.stdout.strip()).resolve()
    return p

def now_iso_bangkok() -> str:
    # Always emit UTC+7 (SE Asia) per project convention.
    tz = datetime.timezone(datetime.timedelta(hours=7))
    return datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S+07:00")

def write_status(repo: Path, agent: str, stage: str,
                 tasks_clear: bool, tasks: list[str], note: str | None) -> Path:
    data_dir = repo / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / f"{agent}.json"

    current: dict = {}
    if target.exists():
        try:
            current = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(f"Error: corrupt JSON in {target}: {e}")

    # Merge: always overwrite mutable fields, preserve anything extra.
    out = {
        "agent": agent,
        "stage": stage,
        "tasks": (tasks if tasks_clear else (current.get("tasks", []) + tasks)),
        "note": note if note is not None else current.get("note", ""),
        "updatedAt": now_iso_bangkok(),
    }
    # Preserve arbitrary extra fields (future-proofing).
    for k, v in current.items():
        if k not in out:
            out[k] = v

    # Stable, 2-space indent, trailing newline — matches existing files.
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return target

def git_ops(repo: Path, files: list[Path], agent: str, stage: str, push: bool) -> None:
    def run(*args, check=True, capture=True) -> subprocess.CompletedProcess:
        res = subprocess.run(args, capture_output=capture, text=True, cwd=str(repo))
        if check and res.returncode != 0:
            msg = (res.stderr or res.stdout or "").strip() or "unknown error"
            raise SystemExit(f"Git error ({' '.join(args)}): {msg}")
        return res

    for f in files:
        run("git", "add", str(f.relative_to(repo).as_posix()))
    run("git", "add", "-A", "data/")
    msg = f"chore(monitor): {agent} -> {stage}"
    run("git", "commit", "-m", msg)
    if push:
        # Multi-agent concurrency guard: fast-forward our commit on top of
        # any remote work, then push. Rebase (not merge) keeps history linear.
        run("git", "pull", "--rebase", "--autostash")
        run("git", "push")

    print(f"[hermes-update-status] OK  agent={agent} stage={stage} "
          f"file={'|'.join(f.name for f in files)} "
          f"updatedAt={now_iso_bangkok()}", file=sys.stderr)

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="hermes-update-status",
        description="Auto-update a per-agent status JSON + git commit/push.",
        add_help=True,
    )
    ap.add_argument("--agent", required=True,
                    help="Agent name (hermes/dev/frontend/security/design).")
    ap.add_argument("--stage", required=True,
                    help="Status stage (idle/working/in-review/blocked/done).")
    ap.add_argument("--task", action="append", default=[],
                    help="Task to record. Repeatable. Use --no-task to clear.")
    ap.add_argument("--no-task", dest="clear_tasks", action="store_true",
                    help="Clear existing tasks before applying --task.")
    ap.add_argument("--note", default=None, help="Free-form status note.")
    ap.add_argument("--repo", default=None, help="Override repo root path.")
    ap.add_argument("--no-push", action="store_true", help="Skip git push.")
    args = ap.parse_args()

    agent = resolve_agent(args.agent)
    repo = repo_root(args.repo)
    target = write_status(
        repo, agent, args.stage, args.clear_tasks, list(args.task), args.note
    )
    git_ops(repo, [target], agent, args.stage, push=not args.no_push)
    return 0

if __name__ == "__main__":
    sys.exit(main())
