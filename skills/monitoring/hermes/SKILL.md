---
name: hermes-monitor
description: Update Hermes orchestrator status to data/hermes.json and push for the live dashboard.
version: 1.0.0
author: Maulana Abdur Rofik, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [monitoring, orchestrator, status, dashboard]
    related_skills: [dev-monitor, frontend-monitor, security-monitor, design-monitor]
triggers:
  - "status hermes"
  - "update hermes"
  - "hermes idle"
  - "hermes working"
  - "hermes blocked"
  - "hermes done"
  - "orchestrator status"
---

# Hermes Monitor Skill

Auto-update Hermes orchestrator status for the live dashboard.

## When to Use

- Hermes finishes or starts any orchestration task
- Any phase change (draft, review, approved, in-progress, done)
- When a blocker appears or clears
- After gating approval

## How to Run

```bash
hermes-update-status --stage <stage> [--task "task"] [--note "note"]
```

## Quick Reference

| Command | Effect |
|---|---|
| `hermes-update-status --stage working --task "Gating PRD" --note "Reviewing"` | Record working task |
| `hermes-update-status --stage idle --no-task --note "Waiting"` | Mark idle |
| `hermes-update-status --stage blocked --task "Waiting on Dev API" --note "Blocked: API contract not ready"` | Mark blocked |
| `hermes-update-status --stage done --no-task --note "PRD v3 approved"` | Mark done |

## Procedure

1. Determine the stage: `idle`, `working`, `in-review`, `blocked`, or `done`.
2. Run `hermes-update-status` with `--stage`, one or more `--task`, and optional `--note`.
3. The skill writes `data/hermes.json` (agent, stage, tasks, note, updatedAt).
4. It runs `git add`, `git commit -m "chore(monitor): hermes -> <stage>"`, then `git pull --rebase --autostash && git push`.
5. Dashboard fetches `data/hermes.json` live.

## Pitfalls

- `--task` is append by default; use `--no-task` to replace the task list.
- Stage names are freeform strings but the dashboard UI expects the five above.
- If push is rejected, the script auto-rebases; a conflict would surface then.

## Verification

```bash
cat data/hermes.json | python -m json.tool
git log --oneline -3
```

Expect the latest commit to read `chore(monitor): hermes -> <stage>`.
