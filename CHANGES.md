# Changes

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
