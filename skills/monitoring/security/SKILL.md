---
name: security-monitor
description: Update Security status to data/security.json and push for the live dashboard.
version: 1.0.0
author: Maulana Abdur Rofik, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, security, audit, status]
    related_skills: [hermes-monitor, dev-monitor, frontend-monitor, design-monitor]
triggers:
  - "status security"
  - "update security"
  - "security idle"
  - "security working"
  - "security blocked"
  - "security done"
  - "sec status"
  - "audit status"
---

# Security Monitor Skill

Auto-update Security status for the live dashboard.

## When to Use

- Security finishes or starts a review/audit task
- A vulnerability finding requires recording
- Before a handoff (Security is the final gate)
- After a compliance or hardening review

## How to Run

```bash
security-update-status --stage <stage> [--task "task"] [--note "note"]
```

## Quick Reference

| Command | Effect |
|---|---|
| `security-update-status --stage working --task "Auth audit" --note "Scanning JWT flows"` | Record working task |
| `security-update-status --stage idle --no-task --note "No open findings"` | Mark idle |
| `security-update-status --stage blocked --task "Waiting on Dev fix" --note "Blocked: CVE-2026-xxxx"` | Mark blocked |
| `security-update-status --stage done --no-task --note "Auth audit passed, green light"` | Mark done |

## Procedure

1. Determine the stage: `idle`, `working`, `in-review`, `blocked`, or `done`.
2. Run `security-update-status` with `--stage`, one or more `--task`, and optional `--note`.
3. The skill writes `data/security.json`.
4. It runs `git add`, `git commit -m "chore(monitor): security -> <stage>"`, then `git pull --rebase --autostash && git push`.
5. Dashboard fetches `data/security.json` live.

## Pitfalls

- `--task` is append by default; use `--no-task` to replace the task list.
- Security is the final gate before handoff — mark done only after review complete.
- If push is rejected, the script auto-rebases.

## Verification

```bash
cat data/security.json | python -m json.tool
git log --oneline -3
```

Expect the latest commit to read `chore(monitor): security -> <stage>`.
