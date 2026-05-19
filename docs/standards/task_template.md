# Agent task instructions (playbook)

Use this document when assigning work to coding agents. Paste the **skeleton** below into your prompt and fill the placeholders.

## Anchor docs (point agents here every time)

- Working rules: [AGENTS.md](AGENTS.md) (same folder)
- Data contracts: [data_contracts.md](data_contracts.md)
- API contracts: [api_contracts.md](api_contracts.md)
- Root entry: [../../AGENTS.md](../../AGENTS.md)

## Main runtime (do not drift)

`run.py` → FastAPI `api.py` (port 8000) + Flask `web/app.py` (port 5000). Browser calls Flask `/api/...` first.

## Language (recommended)

- **English** for the whole prompt is fine and often clearest for agents.
- **Hybrid:** Vietnamese for product intent (“user should be able to…”) + **English technical anchors**: file paths (`web/script.js`), endpoints (`POST /api/find-path`), JSON field names (`blocked_edges`, `path_nodes`).
- Always paste **paths and identifiers literally** from the repo.

## Skeleton (copy into every task)

```text
Context (read first):
- docs/standards/AGENTS.md
- docs/standards/data_contracts.md (if touching data)
- docs/standards/api_contracts.md (if touching HTTP)

Goal:
<one sentence user-visible or API-visible outcome>

Scope (allowed to edit):
- <paths only, e.g. web/map.html, web/style.css>

Non-goals (must not change):
- <e.g. no api.py contract change; no new dependencies>

Requirements:
- <bullets>

Acceptance criteria (testable):
- <bullets>

Constraints:
- Approval-first; minimal diff; follow docs/standards/AGENTS.md

Verify:
- python run.py
- <manual steps, URLs, curl if API>
```

## Template A — Frontend layout / UX

```text
Goal:
<one sentence>

Scope: Only edit:
- web/<files>

Non-goals:
- Do not change api.py request/response contracts
- Do not add npm packages (this project is static JS + Flask)

Requirements:
- <bullets>

Acceptance criteria:
- <bullets>

Verify:
- python run.py
- Open http://localhost:5000 and <steps>

Follow docs/standards/AGENTS.md (approval-first, minimal change).
```

## Template B — API / backend

```text
Goal:
<one sentence>

Scope:
- api.py
- web/app.py (only if proxy/fallback must change)

Contract:
- Update docs/standards/api_contracts.md if request or response shape changes

Acceptance criteria:
- POST /find-path: <cases>
- POST /api/find-path remains compatible with browser unless explicitly changed

Verify:
- <curl or FastAPI /docs steps>
```

## Template C — Data / graph

```text
Goal:
<one sentence>

Scope:
- data/processed/outputs/<files> OR named pipeline scripts

Constraints:
- If JSON schema changes, update docs/standards/data_contracts.md

Acceptance criteria:
- <invariants: fake nodes, transfer edges, connectivity, IDs>
```

## Habits that improve outcomes

- Name **exact files** instead of “the frontend”.
- **One focused task** per thread; split large features into phases.
- Say **“propose plan before editing”** if you want strict approval on the first message.
- Attach **screenshots, errors, or code snippets** when debugging.
- “Done” = all **acceptance criteria** checked, not a vague “looks good”.
