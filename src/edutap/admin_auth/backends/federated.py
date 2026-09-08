"""The wrapper around the estate's federated sign-ins.

`fastapi_auth.saml.SamlSP` and `fastapi_auth.openid.OidcRP` both expose
``current_user()`` -- a callable taking the request and answering a
``FederatedIdentity`` or raising 401 -- and both identity models agree on the
field names they share. One wrapper therefore serves both; `saml.py` and
`oidc.py` are the thin, import-carrying conveniences on top.
"""

from collections.abc import Awaitable, Callable
from typing import Protocol

from fastapi import HTTPException, Request

from ..identity import AdminIdentity
from ..requires import SignInBackend


class FederatedIdentityLike(Protocol):
    """What we read off either package's FederatedIdentity."""

    display_name: str | None
    given_name: str | None
    surname: str | None

    def model_dump(self, **kwargs: object) -> dict[str, object]:
        """Pydantic's serialisation; both models are pydantic models."""
        ...


def federated_backend(
    current_user: Callable[[Request], Awaitable[FederatedIdentityLike]],
    identifier: Callable[[FederatedIdentityLike], str | None],
    groups_from: str = "entitlement",
) -> SignInBackend:
    """Translate a federated sign-in into this library's `SignInBackend`.

    `current_user` is ``sp.current_user()`` / ``rp.current_user()``;
    `identifier` is ``sp.identifier`` / ``rp.identifier`` -- the deployment's
    chosen stable identifier. `groups_from` names what the permission map
    resolves against: a typed list field (`entitlement` by default, the
    eduPersonEntitlement convention) or, failing that, a key in the raw
    ``attributes`` / ``claims`` escape hatch.
    """

    async def identify(request: Request) -> AdminIdentity:
        identity = await current_user(request)
        subject = identifier(identity)
        if subject is None:
            # The person DID sign in; it is the attribute release that is
            # broken -- a configuration matter between IdP and SP that
            # re-signing-in cannot fix, so 403 rather than 401.
            raise HTTPException(403, "The sign-in released no stable identifier for you")
        return AdminIdentity(
            subject=subject,
            display_name=_display_name(identity, subject),
            groups=_groups(identity, groups_from),
            claims=identity.model_dump(),
        )

    return identify


def _display_name(identity: FederatedIdentityLike, subject: str) -> str:
    if identity.display_name:
        return identity.display_name
    parts = [p for p in (identity.given_name, identity.surname) if p]
    return " ".join(parts) if parts else subject


def _groups(identity: FederatedIdentityLike, groups_from: str) -> list[str]:
    typed = getattr(identity, groups_from, None)
    if isinstance(typed, list):
        return [str(value) for value in typed]
    # The escape hatch: `attributes` on the SAML model, `claims` on the OIDC
    # one -- whichever the object carries.
    for hatch in ("attributes", "claims"):
        raw = getattr(identity, hatch, None)
        if isinstance(raw, dict) and groups_from in raw:
            values = raw[groups_from]
            if isinstance(values, list):
                return [str(value) for value in values]
            return [str(values)]
    return []
