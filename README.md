# edutap.admin_auth

Person authentication and per-route permission checks for eduTAP admin APIs.
Part of the eduTAP estate; the design lives in
`edutap.admin_ui/docs/superpowers/specs/2026-09-05-admin-ui-design.md` and in
`edutap.pass_builder/docs/adr/0001-administration-moves-out-of-this-service.md`.

## What it provides

- **`AdminIdentity`** — who is calling: a subject, a display name, and the raw
  claims or attributes the deployment's sign-in produced.
- **A sign-in backend, chosen by configuration.** HTTP Basic for local work and
  tests; `federated_backend` wraps the estate's SAML SP and OIDC RP
  (`fastapi-auth-saml-federated`, `fastapi-auth-openid-federated` -- the
  `[saml]` / `[oidc]` extras):

  ```python
  from edutap.admin_auth import AdminAuth, PermissionMap, federated_backend
  from fastapi_auth import saml

  sp = saml.SamlSP(saml.SamlSettings(...))
  sp.mount(app)
  auth = AdminAuth(
      permission_map=PermissionMap.parse(settings.permissions),
      backend=federated_backend(sp.current_user(), sp.identifier),
  )
  ```

  One caveat, measured on 2026-09-08: the `[saml]` and `[oidc]` extras cannot
  share a virtualenv today. `joserfc>=1.7` (OIDC) requires `cryptography>=45`,
  while `pysaml2` (SAML) caps `pyopenssl` below 24.3, which caps
  `cryptography` below 44. A deployment picks one sign-in anyway; only an
  installation wanting both in one process is affected.
- **A permission map**, from settings: group or claim → permission list.
- **`requires(permission)`** — the FastAPI dependency, resolving the tenant
  from the path.

## Install (development)

```bash
make venv
make test-local
make lint
```
