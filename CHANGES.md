# Changes

## 0.1.0 (unreleased)

- Initial release: `AdminIdentity`, the `object:verb@tenant` permission
  vocabulary, the settings-driven permission map, `requires()`, and the HTTP
  Basic sign-in backend for local work and tests.
- `federated_backend`: one wrapper serving both of the estate's federated
  sign-ins (`fastapi-auth-saml-federated`, `fastapi-auth-openid-federated`),
  behind the `[saml]` / `[oidc]` extras.
