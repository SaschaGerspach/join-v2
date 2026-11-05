# ADR 0001: All board permission checks live in one module

Status: Accepted  
Date: 2026-10-22 (written after the decision, see README)  
Related commits: `2755067`, `d2e4523`

## Context

Many apps need to know if a user may see or change a board: tasks, columns,
labels, automations, webhooks, the WebSocket consumer and more. In the
beginning, views had their own copies of the access check. Copies drift
apart: when a rule changes, it is easy to update some places and forget
others. That is a security risk, because one outdated check is enough to
leak data.

## Decision

All board permission rules live in `backend/boards_api/permissions.py`.
Other apps call these functions (`can_access_board`, `can_edit_board`,
`is_board_admin`, `is_board_owner`, `get_board_or_404`). They do not
check roles or flags like `is_staff` themselves.

## Consequences

- A rule change happens in one place, and every app gets it.
- The permission model can be tested in one place and read in one file.
- `permissions.py` becomes a central dependency. A bug there affects the
  whole API, so changes need tests.
- Developers must remember to use the module. Nothing in the framework
  forces it, so a new view can still skip the check by mistake.

## Alternatives considered

- **Checks inside each view:** simple at the start, but the copies drift
  apart over time. This was the original state.
- **DRF permission classes or a library like django-guardian:** more
  framework support, but the rules here depend on board, team and member
  role together. Plain functions were easier to read and test.
