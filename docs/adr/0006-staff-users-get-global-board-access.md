# ADR 0006: Staff users get access to all boards

Status: Superseded by ADR 0007  
Date: 2026-10-22 (written after the decision, see README)  
Related commits: `de6845b` (2026-04-19)

## Context

The app has a platform admin role (`is_staff`). Admins need to help users
and manage the platform. For that, it seemed useful that they can open any
board.

## Decision

Every permission check lets `is_staff` users pass. Staff users can read and
edit all boards, tasks and comments.

## Consequences

- Support is easy: an admin can look at any board.
- Every admin can read all private content. There is no record of when an
  admin looked at a board.
- The frontend decides what to show based on `is_staff`, not on the real
  rights for a board.

## Alternatives considered

Not recorded. This ADR was written later, after the decision had already
been replaced by ADR 0007.
