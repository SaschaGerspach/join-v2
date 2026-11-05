# ADR 0003: Short-lived access token in memory, rotating refresh token in an HttpOnly cookie

Status: Accepted  
Date: 2026-10-22 (written after the decision, see README)

## Context

The Angular frontend and the Django API run on different origins. The app
uses JWT (djangorestframework-simplejwt). We need to decide where the
tokens live in the browser and how long they are valid.

The main risks:

- **XSS:** if an attacker can run JavaScript on the page, they can read
  everything in `localStorage`.
- **Stolen tokens:** a token that is valid for a long time is valuable
  for an attacker.
- **CSRF:** cookies are sent by the browser automatically, also on
  requests that a foreign page starts.

## Decision

- The **access token** is valid for 5 minutes. The frontend keeps it only
  in memory (a variable in `AuthService`) and sends it in the
  `Authorization` header. It is never written to `localStorage`.
- The **refresh token** is valid for 7 days and lives in an `HttpOnly`
  cookie. JavaScript cannot read it. The cookie path is `/auth/`, so the
  browser only sends it to the auth endpoints, not to every API request.
- **Rotation:** every refresh returns a new refresh token, and the old one
  goes on a blacklist. A stolen refresh token can only be used once.
- **Origin check:** in production the cookie must be `SameSite=None`
  because frontend and API are on different sites. That means a foreign
  page could trigger a refresh. The refresh endpoint therefore rejects
  requests whose `Origin` header is not on the allow list. Requests without
  an `Origin` header are let through; browsers always send it on
  cross-site POST requests, so a foreign page cannot skip the check.
- Logout blacklists the refresh token. Deactivated users cannot refresh.
- Login and other auth endpoints are rate limited (10 per minute in
  production).

## Consequences

- XSS cannot steal the refresh token. But while the page is open,
  injected script can call the refresh endpoint itself (the browser sends
  the cookie) and get new access tokens. This setup limits what an
  attacker can take away, not what they can do during the session.
- After a page reload the access token is gone. The app must call the
  refresh endpoint first. This adds one request at startup.
- Logout is not instant for access tokens: an access token that was
  already issued stays valid until it expires (max. 5 minutes).
- The blacklist table grows with every refresh. There is no cleanup job
  yet (see "Open points").
- More moving parts than a simple "token in localStorage" setup: the
  interceptor must handle 401, refresh and retry.

## Alternatives considered

- **Both tokens in `localStorage`:** simplest, but any XSS steals a
  long-lived token.
- **Django session cookies only:** no JWT at all and easy to revoke, but
  every write request then needs CSRF protection, and cross-site cookies
  (`SameSite=None`) are needed for every request, not only for refresh.
- **Long-lived access token without refresh:** fewer requests, but a stolen
  token is valid for a long time and cannot be revoked.

## Open points

- Expired entries in the token blacklist are never deleted. simplejwt has a
  `flushexpiredtokens` command that could run as a daily Celery Beat task.
- The rate limit identifies clients by `X-Forwarded-For`, but
  `NUM_PROXIES` is not set. A client can send a fake header and bypass the
  limit on login and guest login. This is deliberately deferred while the
  app runs as a demo.
