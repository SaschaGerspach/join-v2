# ADR 0005: Team members can edit team boards, even with a viewer role

Status: Accepted  
Date: 2026-10-22 (written after the decision, see README)

## Context

A board can belong to a team. Users can also be added to a board directly,
with the role viewer, editor or admin. So one person can be both a team
member and a board viewer. We need to decide which rule wins.

## Decision

Team boards are collaborative on purpose. Every member of the board's team
may edit content (tasks, columns, labels, automations, webhooks). An
explicit viewer membership does **not** reduce this right
(`can_edit_board` in `permissions.py`).

Board administration is not given through the team. Managing members,
invite links and the archive still needs the board admin role or ownership
(`is_board_admin`).

If someone wants to share a board read-only, the board must not be in a
team. Then viewers are invited directly.

## Consequences

- Teams work without extra setup: a new team member can work on all team
  boards right away.
- The rule "viewer means read-only" is not true in every case. For someone
  who reads the role list, it looks like a bug. This ADR and a comment in
  the code explain it.
- There is no way to have a read-only person inside a team for one
  specific board.

## Alternatives considered

- **Most restrictive role wins (viewer stays viewer):** more control, but
  team owners must manage roles on every board. This works against the
  idea of a team.
- **Highest role wins, including admin:** simpler, but every team member
  could then manage members and delete invite links. Too much power.
