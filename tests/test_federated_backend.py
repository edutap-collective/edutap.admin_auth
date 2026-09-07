"""The wrapper around the estate's federated sign-ins (SAML SP / OIDC RP)."""

import pytest
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

from edutap.admin_auth.backends.federated import federated_backend


class FakeFederatedIdentity(BaseModel):
    """The shape both federated packages agree on, reduced to what we read."""

    eppn: str | None = None
    display_name: str | None = None
    given_name: str | None = None
    surname: str | None = None
    entitlement: list[str] = Field(default_factory=list)
    attributes: dict[str, list[str]] = Field(default_factory=dict)


def request() -> Request:
    return Request({"type": "http", "method": "GET", "url": "http://t/", "headers": []})


def backend_answering(identity, identifier=lambda i: i.eppn):
    async def current_user(request: Request):
        return identity

    return federated_backend(current_user, identifier)


async def test_maps_identifier_display_name_and_entitlements():
    identity = FakeFederatedIdentity(
        eppn="jdoe@lmu.de",
        display_name="J. Doe",
        entitlement=["urn:mace:example:admin"],
    )
    admin = await backend_answering(identity)(request())
    assert admin.subject == "jdoe@lmu.de"
    assert admin.display_name == "J. Doe"
    assert admin.groups == ["urn:mace:example:admin"]


async def test_display_name_falls_back_to_given_and_surname_then_subject():
    named = FakeFederatedIdentity(eppn="a@b", given_name="Jo", surname="Doe")
    assert (await backend_answering(named)(request())).display_name == "Jo Doe"
    bare = FakeFederatedIdentity(eppn="a@b")
    assert (await backend_answering(bare)(request())).display_name == "a@b"


async def test_groups_can_come_from_a_raw_attribute_instead():
    identity = FakeFederatedIdentity(eppn="a@b", attributes={"memberOf": ["cn=ub-admins"]})

    async def current_user(request: Request):
        return identity

    admin = await federated_backend(current_user, lambda i: i.eppn, groups_from="memberOf")(
        request()
    )
    assert admin.groups == ["cn=ub-admins"]


async def test_no_stable_identifier_is_a_403_not_a_401():
    # The person DID sign in; it is the attribute release that is broken --
    # a configuration matter between IdP and SP, not something re-signing-in fixes.
    identity = FakeFederatedIdentity(display_name="J. Doe")
    with pytest.raises(HTTPException) as error:
        await backend_answering(identity)(request())
    assert error.value.status_code == 403


async def test_the_sign_ins_401_passes_through():
    async def current_user(request: Request):
        raise HTTPException(401, "Not authenticated")

    with pytest.raises(HTTPException) as error:
        await federated_backend(current_user, lambda i: None)(request())
    assert error.value.status_code == 401


async def test_the_raw_attributes_reach_the_claims():
    identity = FakeFederatedIdentity(eppn="a@b", attributes={"mail": ["a@b"]})
    admin = await backend_answering(identity)(request())
    assert admin.claims["attributes"] == {"mail": ["a@b"]}
