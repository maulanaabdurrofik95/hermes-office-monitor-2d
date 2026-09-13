---
name: design-monitor
description: Update Design status to data/design.json and push for the live dashboard.
version: 1.0.0
author: Maulana Abdur Rofik, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, design, UX, status]
    related_skills: [hermes-monitor, dev-monitor, frontend-monitor, security-monitor]
triggers:
  - "status design"
  - "update design"
  - "design idle"
  - "design working"
  - "design blocked"
  - "design done"
  - "ui status"
  - "ux status"
---

# Design Monitor Skill

Auto-update Design status for the live dashboard.

## When to Use

- Design finishes or starts a wireframe/mockup/style-guide task
- A design-system token or brand guideline update
- Before handing off to Frontend for implementation
- After a UX review or user-flow revision

## How to Run

```bash
design-update-status --stage <stage> [--task "task"] [--note "note"]
```

## Quick Reference

| Command | Effect |
|---|---|
| `design-update-status --stage working --task "Wireframes" --note "Updating onboarding flow"` | Record working task |
| `design-update-status --stage idle --no-task --note "Waiting for brief"` | Mark idle |
| `design-update-status --stage blocked --task "Waiting on Dev" --note "Blocked: API fields undefined"` | Mark blocked |
| `design-update-status --stage done --no-task --note "Wireframes shipped to Frontend"` | Mark done |

## Procedure

1. Determine the stage: `idle`, `working`, `in-review`, `blocked`, or `done`.
2. Run `design-update-status` with `--stage`, one or more `--task`, and optional `--note`.
3. The skill writes `data/design.json`.
4. It runs `git add`, `git commit -m "chore(monitor): design -> <stage>"`, then `git pull --rebase --autostash && git push`.
5. Dashboard fetches `data/design.json` live.

## Pitfalls

- `--task` is append by default; use `--no-task` to replace the task list.
- Design handoff to Frontend is the common transition — note it clearly.
- If push is rejected, the script auto-rebases.

## Verification

```bash
cat data/design.json | python -m json.tool
git log --oneline -3
```

Expect the latest commit to read `chore(monitor): design -> <stage>`.
