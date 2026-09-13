---
name: frontend-monitor
description: Update Frontend status to data/frontend.json and push for the live dashboard.
version: 1.0.0
author: Maulana Abdur Rofik, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, frontend, UI, status]
    related_skills: [hermes-monitor, dev-monitor, security-monitor, design-monitor]
triggers:
  - "status frontend"
  - "update frontend"
  - "frontend idle"
  - "frontend working"
  - "frontend blocked"
  - "frontend done"
  - "ui status"
  - "update ui"
---

# Frontend Monitor Skill

Auto-update Frontend status for the live dashboard.

## When to Use

- Frontend finishes or starts a UI/task
- Canvas rendering, component work, styling changes
- When integrating a new Dev API endpoint
- After deploying a frontend change

## How to Run

```bash
frontend-update-status --stage <stage> [--task "task"] [--note "note"]
```

## Quick Reference

| Command | Effect |
|---|---|
| `frontend-update-status --stage working --task "Building canvas" --task "Implement render engine" --note "Render engine v2"` | Record working tasks |
| `frontend-update-status --stage idle --no-task --note "Canvas shipped, waiting for ticket"` | Mark idle |
| `frontend-update-status --stage blocked --task "Waiting on Dev API" --note "Blocked: /api/items not ready"` | Mark blocked |
| `frontend-update-status --stage done --no-task --note "Canvas + render engine done"` | Mark done |

## Procedure

1. Determine the stage: `idle`, `working`, `in-review`, `blocked`, or `done`.
2. Run `frontend-update-status` with `--stage`, one or more `--task`, and optional `--note`.
3. The skill writes `data/frontend.json`.
4. It runs `git add`, `git commit -m "chore(monitor): frontend -> <stage>"`, then `git pull --rebase --autostash && git push`.
5. Dashboard fetches `data/frontend.json` live.

## Pitfalls

- `--task` is append by default; use `--no-task` to replace the task list.
- Frontend is the primary visible agent — keep tasks concise for the dashboard panel.
- If push is rejected, the script auto-rebases.

## Verification

```bash
cat data/frontend.json | python -m json.tool
git log --oneline -3
```

Expect the latest commit to read `chore(monitor): frontend -> <stage>`.
