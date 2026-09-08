# Changes

## 0.2.0 (unreleased)

- `AdminAuth.check(request, permission)`: the imperative twin of `requires()`,
  for host-side seams that declare permissions on routes mounted in several
  applications. Same semantics; a malformed permission literal raises at the
  host instead of masquerading as a caller's 400.

## 0.1.0 (unreleased)

- Initial release: `AdminIdentity`, the `object:verb@tenant` permission
  vocabulary, the settings-driven permission map, `requires()`, and the HTTP
  Basic sign-in backend for local work and tests.
- `trusted_header_backend`: the back-office pattern -- a person authenticated
  at the web frontend and asserted by headers; wired through settings
  (`backend = "trusted_header"`, `EDUTAP_ADMIN_AUTH_TRUSTED_*`).
- `federated_backend`: one wrapper serving both of the estate's federated
  sign-ins (`fastapi-auth-saml-federated`, `fastapi-auth-openid-federated`),
  behind the `[saml]` / `[oidc]` extras.
