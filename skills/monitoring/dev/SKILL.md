---
name: dev-monitor
description: Update Dev backend status to data/dev.json and push for the live dashboard.
version: 1.0.0
author: Maulana Abdur Rofik, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, backend, dev, status]
    related_skills: [hermes-monitor, frontend-monitor, security-monitor, design-monitor]
triggers:
  - "status dev"
  - "update dev"
  - "dev idle"
  - "dev working"
  - "dev blocked"
  - "dev done"
  - "backend status"
  - "update backend"
---

# Dev Monitor Skill

Auto-update Dev backend status for the live dashboard.

## When to Use

- Dev finishes or starts a backend/infrastructure task
- API contract changes, database migrations, CI/CD updates
- Security flag requiring backend attention
- When Dev is waiting on a frontend integration

## How to Run

```bash
dev-update-status --stage <stage> [--task "task"] [--note "note"]
```

## Quick Reference

| Command | Effect |
|---|---|
| `dev-update-status --stage working --task "Auth endpoint" --note "Implementing JWT"` | Record working task |
| `dev-update-status --stage idle --no-task --note "Waiting for API spec"` | Mark idle |
| `dev-update-status --stage blocked --task "Waiting on Frontend" --note "Blocked: UI spec pending"` | Mark blocked |
| `dev-update-status --stage done --no-task --note "Auth endpoint shipped"` | Mark done |

## Procedure

1. Determine the stage: `idle`, `working`, `in-review`, `blocked`, or `done`.
2. Run `dev-update-status` with `--stage`, one or more `--task`, and optional `--note`.
3. The skill writes `data/dev.json`.
4. It runs `git add`, `git commit -m "chore(monitor): dev -> <stage>"`, then `git pull --rebase --autostash && git push`.
5. Dashboard fetches `data/dev.json` live.

## Pitfalls

- `--task` is append by default; use `--no-task` to replace the task list.
- Dev has a standing note about v1 frontend-only scope — update it when backend work starts.
- If push is rejected, the script auto-rebases.

## Verification

```bash
cat data/dev.json | python -m json.tool
git log --oneline -3
```

Expect the latest commit to read `chore(monitor): dev -> <stage>`.
