"""HTTP Basic: the sign-in for local work and tests."""

import base64

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from edutap.admin_auth.backends.basic import BasicUser, basic_backend
from edutap.admin_auth.permissions import PermissionMap
from edutap.admin_auth.requires import AdminAuth

USERS = {
    "jdoe": BasicUser(password="s3cret", display_name="J. Doe", groups=["ub-admins"]),
}
MAP = PermissionMap.parse({"ub-admins": ["templates:read@lmu-ub"]})


def client() -> TestClient:
    auth = AdminAuth(permission_map=MAP, backend=basic_backend(USERS))
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {}

    return TestClient(app)


def basic(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_no_credentials_answer_401_with_a_basic_challenge():
    response = client().get("/tenants/lmu-ub/templates")
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")


def test_a_wrong_password_answers_401():
    response = client().get("/tenants/lmu-ub/templates", headers=basic("jdoe", "wrong"))
    assert response.status_code == 401


def test_an_unknown_user_answers_401():
    response = client().get("/tenants/lmu-ub/templates", headers=basic("who", "s3cret"))
    assert response.status_code == 401


def test_valid_credentials_reach_the_route():
    response = client().get("/tenants/lmu-ub/templates", headers=basic("jdoe", "s3cret"))
    assert response.status_code == 200


def test_the_identity_carries_the_users_groups_and_display_name():
    auth = AdminAuth(permission_map=MAP, backend=basic_backend(USERS))
    app = FastAPI()

    @app.get("/tenants/{tenant_id}/whoami")
    async def whoami(
        tenant_id: str,
        identity=Depends(auth.requires("templates:read")),
    ) -> dict:
        return {"subject": identity.subject, "display_name": identity.display_name}

    body = TestClient(app).get("/tenants/lmu-ub/whoami", headers=basic("jdoe", "s3cret")).json()
    assert body == {"subject": "jdoe", "display_name": "J. Doe"}
