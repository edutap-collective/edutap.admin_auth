"""HTTP Basic sign-in, for local work and tests.

Deliberately not for a deployment: the deployment backends wrap the estate's
federated SAML and OIDC packages. This one exists so a service and its tests
can run without an identity provider in the room.
"""

import base64
import binascii
import secrets

from fastapi import HTTPException, Request
from pydantic import BaseModel, SecretStr

from ..identity import AdminIdentity
from ..requires import SignInBackend

_CHALLENGE = {"WWW-Authenticate": 'Basic realm="admin"'}


class BasicUser(BaseModel):
    """One locally declared person: password, display name, groups."""

    password: SecretStr
    display_name: str
    groups: list[str]


def basic_backend(users: dict[str, BasicUser]) -> SignInBackend:
    """Return a sign-in backend answering from the given user table."""

    async def identify(request: Request) -> AdminIdentity:
        username, password = _credentials_from(request)
        user = users.get(username)
        # The password comparison runs even for an unknown user, against an
        # empty string, so the two refusals take the same time and carry the
        # same message -- a caller learns nothing about which half was wrong.
        expected = user.password.get_secret_value() if user is not None else ""
        if not secrets.compare_digest(password, expected) or user is None:
            raise HTTPException(401, "Wrong credentials", headers=_CHALLENGE)
        return AdminIdentity(subject=username, display_name=user.display_name, groups=user.groups)

    return identify


def _credentials_from(request: Request) -> tuple[str, str]:
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        raise HTTPException(401, "Sign in", headers=_CHALLENGE)
    try:
        decoded = base64.b64decode(header.removeprefix("Basic "), validate=True).decode()
        username, _, password = decoded.partition(":")
    except (binascii.Error, UnicodeDecodeError) as error:
        raise HTTPException(401, "Sign in", headers=_CHALLENGE) from error
    return username, password
