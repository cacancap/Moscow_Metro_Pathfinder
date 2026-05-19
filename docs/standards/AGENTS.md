# AGENTS Working Rules

This file defines mandatory rules for AI agents working in this repository.

## 0) How to assign tasks (human → agent)

For every task prompt, start with the **Goal / Scope / Non-goals / Acceptance / Verify** skeleton and link the anchor docs. Copy from [task_template.md](task_template.md). Prefer **English** for technical anchors (paths, endpoints, field names); product intent may be Vietnamese if you want.

## 1) Approval-First Policy

- Do not modify code, configuration, or data files unless the user explicitly approves the change.
- For non-trivial work, propose the plan first and wait for approval before editing.
- If requirements are unclear, ask before implementing.

## 2) Minimal and Optimal Change Principle

- Always prefer the smallest valid change that fully solves the requested problem.
- Avoid broad refactors when a focused fix is sufficient.
- Keep behavior stable unless behavior change is explicitly requested.

## 3) Explain Logic and Commands Clearly

- After each implementation task, report:
  - What changed and why.
  - The logic of how the updated flow works.
  - The commands used for verification (run/test/start) and key outcomes.
- When introducing a new command, include a short explanation of its purpose.

## 4) Main Runtime Flow (Source of Truth)

Treat this runtime as the primary production flow:

1. `python run.py`
2. `run.py` starts:
   - FastAPI backend: `uvicorn api:app --host 127.0.0.1 --port 8000 --reload`
   - Flask frontend: `python web/app.py` (port 5000)

Files not in this flow should not be changed unless the user requests it.

## 5) Safety and Scope

- Do not run destructive operations.
- Do not commit or push unless explicitly requested by the user.
- Preserve existing style and file organization.
- Keep docs consistent with the actual runtime behavior.

## 6) Completion Checklist

Before marking work done:

- Confirm the change follows approval-first and minimal-change principles.
- Confirm runtime flow remains valid (`run.py` -> `api.py` + `web/app.py`).
- Provide concise verification notes and any follow-up risks.
