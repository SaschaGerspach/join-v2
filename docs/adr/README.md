# Architecture Decision Records

This folder records important technical decisions in Join: what was
decided, why, and what it costs. The format follows Michael Nygard's ADR
template.

Not every decision gets an ADR. Only decisions that look wrong without an
explanation, had real alternatives, are expensive to change, or accept a
clear downside.

**Note on dates:** these records were written after the decisions were
made. The `Date` field shows when the record was written. Where possible,
`Related commits` points to the commits where the decision happened.

**Rule:** an accepted ADR is not edited later. If a decision changes, a
new ADR replaces it, and the old one gets the status "Superseded".
Fixing factual errors or adding missing context is allowed, as long as
the decision itself does not change.

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-central-permission-module.md) | All board permission checks live in one module | Accepted |
| [0002](0002-404-instead-of-403.md) | Return 404, not 403, when a user has no access to a board | Accepted |
| [0003](0003-token-strategy.md) | Short-lived access token in memory, rotating refresh token in an HttpOnly cookie | Accepted |
| [0004](0004-websocket-auth-via-first-message.md) | WebSocket clients authenticate with the first message, not in the URL | Accepted |
| [0005](0005-team-members-edit-team-boards.md) | Team members can edit team boards, even with a viewer role | Accepted |
| [0006](0006-staff-users-get-global-board-access.md) | Staff users get access to all boards | Superseded by 0007 |
| [0007](0007-staff-is-platform-admin-only.md) | Staff is a platform admin role, not a content role | Accepted |
| [0008](0008-automation-loop-guard.md) | Run automations synchronously with a thread-local loop guard | Accepted |
