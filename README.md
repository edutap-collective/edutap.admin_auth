# edutap.admin_auth

Person authentication and per-route permission checks for eduTAP admin APIs.
Part of the eduTAP estate; the design lives in
`edutap.admin_ui/docs/superpowers/specs/2026-09-05-admin-ui-design.md` and in
`edutap.pass_builder/docs/adr/0001-administration-moves-out-of-this-service.md`.

## What it provides

- **`AdminIdentity`** — who is calling: a subject, a display name, and the raw
  claims or attributes the deployment's sign-in produced.
- **A sign-in backend, chosen by configuration.** HTTP Basic for local work and
  tests; SAML and OIDC wrappers follow.
- **A permission map**, from settings: group or claim → permission list.
- **`requires(permission)`** — the FastAPI dependency, resolving the tenant
  from the path.

## Install (development)

```bash
make venv
make test-local
make lint
```
