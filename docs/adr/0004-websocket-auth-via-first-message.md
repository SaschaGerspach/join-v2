# ADR 0004: WebSocket clients authenticate with the first message, not in the URL

Status: Accepted  
Date: 2026-10-22 (written after the decision, see README)  
Related commits: `7596dbd`, `f2e3979`

## Context

The board uses WebSockets (Django Channels) for live updates. A WebSocket
connection does not go through the normal DRF authentication. Browsers
also cannot set an `Authorization` header when they open a WebSocket.

The common workaround is to put the token in the URL
(`/ws/board/1/?token=...`). But URLs end up in proxy logs, server logs and
monitoring tools. The token would be stored in many places.

## Decision

- The server accepts the connection first, but sends no data.
- The client must send `{"type": "authenticate", "token": "<access token>"}`
  as its first message.
- The consumer checks the token itself (`AccessToken`), checks that the
  user is active, and checks board access with `can_access_board` from
  `permissions.py` (see ADR 0001).
- Only after that the connection joins the board group and receives events.
- If no valid authenticate message arrives within 10 seconds, the server
  closes the connection (code 4408). A wrong token closes it with 4401.
- The ASGI app also checks the `Origin` header against the allowed origins.

## Consequences

- The token never appears in a URL or in access logs.
- The connection is open for a short time before it is authenticated. The
  timeout limits how long unauthenticated connections can stay open.
- The token is only checked when the connection starts. If the access token
  expires later, the connection stays open.
- Access is also only checked at the start. If a user is removed from a
  board while connected, they keep receiving events until they reconnect.
  This is a known gap (see "Open points").

## Alternatives considered

- **Token in the query string:** simple and common, but it leaks the token
  into logs.
- **Cookie-based auth for WebSockets:** the browser sends cookies
  automatically, also when a foreign page opens the connection
  (cross-site WebSocket hijacking). The app has no auth cookie for normal
  requests anyway (see ADR 0003).
- **`Sec-WebSocket-Protocol` header as token carrier:** works, but misuses
  a header that has a different purpose.

## Open points

Removing a member does not close their open connections. A fix would be to
send a "revoke" event to the board group when a member is removed, so the
consumer of that user can close itself.
