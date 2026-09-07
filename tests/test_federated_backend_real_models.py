"""The wrapper against the real federated identity models, not fakes.

A fake can drift from the packages it imitates; these tests pin the contract:
the field names the wrapper reads exist on both models, and each package's
`select_identifier` works as the `identifier` argument.
"""

import pytest
from fastapi import Request

from edutap.admin_auth.backends.federated import federated_backend

# importorskip per test, not per module: the [saml] and [oidc] extras cannot
# share a venv today (joserfc>=1.7 needs cryptography>=45, pysaml2 caps it
# below 44 via pyopenssl), so whichever is absent must skip only its own test.


def request() -> Request:
    # A complete minimal HTTP scope: the backend under test only reads
    # headers today, but an incomplete scope would turn any future access to
    # request.url or request.path into a KeyError inside the test.
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )


async def test_wraps_the_saml_identity_model():
    saml_identity = pytest.importorskip("fastapi_auth.saml.identity.model")
    saml_identifier = pytest.importorskip("fastapi_auth.saml.identity.identifier")
    identity = saml_identity.FederatedIdentity(
        eppn="jdoe@lmu.de",
        display_name="J. Doe",
        entitlement=["urn:mace:example:admin"],
        attributes={"memberOf": ["cn=ub-admins"]},
    )

    async def current_user(request: Request):
        return identity

    def identifier(identity):
        return saml_identifier.select_identifier(identity, "subject_id", ["eppn"])

    admin = await federated_backend(current_user, identifier)(request())
    assert admin.subject == "jdoe@lmu.de"
    assert admin.groups == ["urn:mace:example:admin"]
    assert admin.claims["attributes"] == {"memberOf": ["cn=ub-admins"]}


async def test_wraps_the_oidc_identity_model_with_groups_from_a_claim():
    oidc_identity = pytest.importorskip("fastapi_auth.openid.identity.model")
    oidc_identifier = pytest.importorskip("fastapi_auth.openid.identity.identifier")
    identity = oidc_identity.FederatedIdentity(
        sub="abc123",
        display_name="J. Doe",
        claims={"groups": ["ub-admins"]},
    )

    async def current_user(request: Request):
        return identity

    def identifier(identity):
        return oidc_identifier.select_identifier(identity, "sub", ["eppn"])

    admin = await federated_backend(current_user, identifier, groups_from="groups")(request())
    assert admin.subject == "abc123"
    assert admin.groups == ["ub-admins"]
