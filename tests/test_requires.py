"""requires(permission): the per-route check, tenant resolved from the path."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from edutap.admin_auth.identity import AdminIdentity
from edutap.admin_auth.permissions import PermissionMap
from edutap.admin_auth.requires import AdminAuth

UB_ADMIN = AdminIdentity(
    subject="admin@example.org",
    display_name="A. Admin",
    groups=["ub-admins"],
)

MAP = PermissionMap.parse(
    {
        "ub-admins": ["templates:write@lmu-ub", "templates:read@lmu-ub"],
        "stwm-admins": ["templates:write@stwm"],
    }
)


def app_with(identity: AdminIdentity) -> TestClient:
    auth = AdminAuth(permission_map=MAP)
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {"tenant": tenant_id}

    @app.post(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:write"))],
    )
    async def create_template(tenant_id: str) -> dict:
        return {"tenant": tenant_id}

    @app.get("/no-tenant", dependencies=[Depends(auth.requires("templates:read"))])
    async def no_tenant() -> dict:
        return {}

    app.dependency_overrides[auth.current_identity] = lambda: identity
    return TestClient(app, raise_server_exceptions=False)


def test_allows_the_permission_the_caller_holds_in_that_tenant():
    assert app_with(UB_ADMIN).get("/tenants/lmu-ub/templates").status_code == 200


def test_refuses_the_same_permission_in_another_tenant():
    response = app_with(UB_ADMIN).get("/tenants/stwm/templates")
    assert response.status_code == 403


def test_the_refusal_names_what_was_missing():
    detail = app_with(UB_ADMIN).get("/tenants/stwm/templates").json()["detail"]
    assert "templates:read@stwm" in detail


def test_read_does_not_imply_write():
    reader = AdminIdentity(subject="r@example.org", display_name="R", groups=["nobody"])
    assert app_with(reader).post("/tenants/lmu-ub/templates").status_code == 403


def test_a_route_without_a_tenant_segment_is_a_construction_error_not_a_403():
    # 500, loudly: the route was mounted outside a tenant path, which is a
    # mistake in the service, not a caller who may be talked away with 403.
    assert app_with(UB_ADMIN).get("/no-tenant").status_code == 500


def test_the_identity_reaches_the_route_when_asked_for():
    auth = AdminAuth(permission_map=MAP)
    app = FastAPI()

    @app.get("/tenants/{tenant_id}/whoami")
    async def whoami(
        tenant_id: str,
        identity: AdminIdentity = Depends(auth.requires("templates:read")),
    ) -> dict:
        return {"subject": identity.subject}

    app.dependency_overrides[auth.current_identity] = lambda: UB_ADMIN
    client = TestClient(app)
    assert client.get("/tenants/lmu-ub/whoami").json() == {"subject": "admin@example.org"}


def test_a_configured_tenant_resolver_maps_the_path_value_to_the_permission_tenant():
    # The pass builder's admin routes carry a tenant UUID in the path while
    # permissions carry the tenant key; the resolver is that translation.
    async def resolver(request, path_value: str) -> str:
        assert request.url.path.startswith("/tenants/")
        return {"3f9a": "lmu-ub"}[path_value]

    auth = AdminAuth(permission_map=MAP, tenant_resolver=resolver)
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {}

    app.dependency_overrides[auth.current_identity] = lambda: UB_ADMIN
    assert TestClient(app).get("/tenants/3f9a/templates").status_code == 200


def test_without_a_backend_current_identity_answers_401():
    auth = AdminAuth(permission_map=MAP)
    app = FastAPI()

    @app.get(
        "/tenants/{tenant_id}/templates",
        dependencies=[Depends(auth.requires("templates:read"))],
    )
    async def list_templates(tenant_id: str) -> dict:
        return {}

    assert TestClient(app).get("/tenants/lmu-ub/templates").status_code == 401


def test_a_tenant_segment_the_permission_form_cannot_carry_is_a_400():
    # ':' and '@' cannot appear in the tenant half of a permission; a path
    # like /tenants/a:b/... is a caller's malformed input, not a server error.
    response = app_with(UB_ADMIN).get("/tenants/a:b/templates")
    assert response.status_code == 400
