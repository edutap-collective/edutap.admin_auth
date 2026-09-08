"""Configuration: the backend choice and the permission map, from the environment."""

import base64

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from edutap.admin_auth.permissions import MalformedPermission
from edutap.admin_auth.requires import AdminAuth
from edutap.admin_auth.settings import AdminAuthSettings

ENV = {
    "EDUTAP_ADMIN_AUTH_BACKEND": "basic",
    "EDUTAP_ADMIN_AUTH_PERMISSIONS": '{"ub-admins": ["templates:read@lmu-ub"]}',
    "EDUTAP_ADMIN_AUTH_BASIC_USERS": (
        '{"jdoe": {"password": "s3cret", "display_name": "J. Doe", "groups": ["ub-admins"]}}'
    ),
}


def test_settings_load_from_the_environment(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    settings = AdminAuthSettings()
    assert settings.backend == "basic"
    assert settings.permissions == {"ub-admins": ["templates:read@lmu-ub"]}
    assert settings.basic_users["jdoe"].display_name == "J. Doe"


def test_the_backend_choice_has_no_default(monkeypatch):
    # Which sign-in guards the admin API is a deployment decision; a default
    # would make it an accident.
    monkeypatch.delenv("EDUTAP_ADMIN_AUTH_BACKEND", raising=False)
    with pytest.raises(ValidationError, match="backend"):
        AdminAuthSettings()


def test_from_settings_wires_a_working_basic_sign_in(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    auth = AdminAuth.from_settings(AdminAuthSettings())
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {}

    token = base64.b64encode(b"jdoe:s3cret").decode()
    client = TestClient(app)
    assert client.get("/tenants/lmu-ub/templates").status_code == 401
    assert (
        client.get(
            "/tenants/lmu-ub/templates", headers={"Authorization": f"Basic {token}"}
        ).status_code
        == 200
    )


def test_a_malformed_permission_in_settings_fails_at_wiring_time(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("EDUTAP_ADMIN_AUTH_PERMISSIONS", '{"g": ["templates:write"]}')
    with pytest.raises(MalformedPermission, match="'g'"):
        AdminAuth.from_settings(AdminAuthSettings())


def test_from_settings_wires_the_trusted_header_backend(monkeypatch):
    monkeypatch.setenv("EDUTAP_ADMIN_AUTH_BACKEND", "trusted_header")
    monkeypatch.setenv("EDUTAP_ADMIN_AUTH_PERMISSIONS", '{"ub-admins": ["templates:read@lmu-ub"]}')
    monkeypatch.setenv("EDUTAP_ADMIN_AUTH_TRUSTED_USER_HEADER", "x-shib-eppn")
    monkeypatch.setenv("EDUTAP_ADMIN_AUTH_TRUSTED_GROUPS_HEADER", "x-shib-groups")
    auth = AdminAuth.from_settings(AdminAuthSettings())
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {}

    client = TestClient(app)
    assert client.get("/tenants/lmu-ub/templates").status_code == 401
    assert (
        client.get(
            "/tenants/lmu-ub/templates",
            headers={"x-shib-eppn": "jdoe", "x-shib-groups": "ub-admins"},
        ).status_code
        == 200
    )
