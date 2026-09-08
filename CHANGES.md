# Changes

## 0.1.0 (2026-09-08)

The first release; nothing was tagged before it, so everything below is new.

- Initial release: `AdminIdentity`, the `object:verb@tenant` permission
  vocabulary, the settings-driven permission map, `requires()`, and the HTTP
  Basic sign-in backend for local work and tests.
- `trusted_header_backend`: the back-office pattern -- a person authenticated
  at the web frontend and asserted by headers; wired through settings
  (`backend = "trusted_header"`, `EDUTAP_ADMIN_AUTH_TRUSTED_*`).
- `federated_backend`: one wrapper serving both of the estate's federated
  sign-ins (`fastapi-auth-saml-federated`, `fastapi-auth-openid-federated`),
  behind the `[saml]` / `[oidc]` extras.
- `AdminAuth.check(request, permission)`: the imperative twin of `requires()`,
  for host-side seams that declare permissions on routes mounted in several
  applications. Same semantics; a malformed permission literal raises at the
  host instead of masquerading as a caller's 400.
- The tenant resolver receives the request (`resolver(request, path_value)`):
  a host's UUID-to-key translation needs the request's context, above all its
  database session.
