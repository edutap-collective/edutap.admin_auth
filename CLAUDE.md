# CLAUDE.md — edutap.admin_auth

Repository-specific rules. They take precedence over the global defaults.

## Language

**English only.** This repository belongs to eduTAP proper, not to any single
institution: README, changelog, documentation, docstrings, code comments, commit
messages, pull request titles and bodies, and replies to review comments.

The language follows the repository, not the conversation. A discussion held in
German still produces English artefacts here.

## What this library is

Person authentication and per-route permission checks for eduTAP admin APIs:
`AdminIdentity`, a sign-in backend chosen by configuration, a settings-driven
permission map, and `requires()`. It is a library — it runs no server, owns no
routes beyond what a backend needs for its sign-in, and stores nothing.

The design it implements is recorded in
`edutap.admin_ui/docs/superpowers/specs/2026-09-05-admin-ui-design.md` and in
`edutap.pass_builder/docs/adr/0001-administration-moves-out-of-this-service.md`.

## Guard rails

**No user store, no role editor, no permission table — ever.** Every one of those
would put authorisation in N places and make an ex-colleague's removal an N-step
job. Who may do what comes from the deployment's settings (the vault, the deploy
diff) and from the identity provider's groups; this library only reads it.

**`current_identity` is the one place a person is established, and it must stay a
single, stable function object.** FastAPI's `dependency_overrides` keys on object
identity, and every `requires(...)` call produces a distinct dependency. The pass
builder learnt this the hard way with `current_auth`; a refactor that turns the
seam back into a per-call product silently breaks every test and every service
that overrides it.

**The tenant lives inside the permission, never beside it.** `templates:write@lmu-ub`
can say that the university library's administrator has no business in the student
union; a permission without the tenant cannot. Nothing in this library may compare
an `object:verb` pair while ignoring the tenant half.

**A malformed permission is a startup failure, not a quiet denial.** The map is
validated when it is wired (`from_settings`, `PermissionMap.parse`) and a
`requires()` argument at import time. A typo that only surfaced as a 403 would
read as a missing grant and be "fixed" by widening somebody's rights.

## Sources and confidentiality

**No vendor internals — from any vendor, not just the ones currently in play.**
Neither in files nor in commit messages.

The standard is academic: a statement counts as reliable only where it can be
evidenced from public information, with a link. Everything else was obtained either
by our own testing or through insider knowledge, and the three are not
interchangeable:

* **Documented** — public source, linked. May be written as fact.
* **Verified, not citable** — obtained by a person from an access-protected area and
  checked there; the reference is recorded internally but must not be published; and
  the statement has been reduced to what is not confidential. May be written as fact,
  carrying this label. It is the rule journalism uses for source protection: the claim
  stands, we know where it comes from, the reader does not get the source.

  The four conditions hold together. A statement for which nobody can name the
  internal reference does not fall here — that is insider knowledge.
* **Measured** — established by our own tests. May be written down, but always marked
  as such, because it describes what a platform did on the day we looked, not what it
  guarantees. It can change with the next release, without notice and without an
  entry in any changelog.
* **Insider knowledge** — is not written down at all.

What a platform's behaviour *means for us* stays documentable even where the
mechanism does not: "the platform enforces a deadline, it is self-healing, it is
outside our control" carries the design consequence without disclosing anything.

Contract and regulatory material is wanted and citable: eduPersonAssurance, GÉANT and
eduGAIN terms, published wallet programme obligations.

## Working practice

Branch first, never commit on `main`. Push only when asked. `make lint` and
`make test-local` green before opening a pull request.

Design records under `docs/superpowers/` record a decision at a point in time — do
not rewrite them to match a later state; write a new one.
