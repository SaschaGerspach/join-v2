# ADR 0007: Staff is a platform admin role, not a content role

Status: Accepted (supersedes ADR 0006)  
Date: 2026-10-22 (written after the decision, see README)  
Related commits: `2fa8d2e` (2026-06-19)

## Context

ADR 0006 gave every `is_staff` user full access to all boards. This had
two problems:

- Platform administration (users, AI feature toggles) and reading private
  board content are different things. Most admins only need the first.
- Admins could read private boards without any trace.

## Decision

- `is_staff` means **platform admin**: admin dashboard, AI feature toggles,
  user account management. Through the API, staff users do not see board
  or team content. The dashboard shows only board metadata (title, color,
  task count, last activity).
- Only `is_superuser` keeps a cross-board override, as an emergency tool.
- When a superuser opens a foreign board or team, this is written to the
  audit log (`superuser_board_access`, `superuser_team_access`). Every
  successful write request by a staff user is logged as `admin_action`.
- The frontend shows actions based on per-board permission flags from the
  API, not based on `is_staff`.

## Consequences

- Private content is protected also from most admins.
- Emergency access still exists, but it leaves a trace.
- Not every superuser read is audited: the board list and sub-resources
  are not logged one by one. Only opening a board or team detail is.
- Support needs more steps: an admin must be invited to a board, or use a
  superuser account.

## Alternatives considered

- **Keep ADR 0006 and add an audit log:** fixes the missing trace, but
  every admin can still read everything.
- **No override at all, also not for superusers:** most private, but in an
  emergency nobody could help.
