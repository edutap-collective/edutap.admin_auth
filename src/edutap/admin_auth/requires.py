"""The per-route permission check, and the seam it hangs on."""

import inspect
from collections.abc import Awaitable, Callable, Coroutine
from typing import TYPE_CHECKING, Any

from fastapi import Depends, HTTPException, Request

from .identity import AdminIdentity
from .permissions import MalformedPermission, Permission, PermissionMap

if TYPE_CHECKING:
    from .settings import AdminAuthSettings

TenantResolver = Callable[[str], str | Awaitable[str]]

SignInBackend = Callable[[Request], Awaitable[AdminIdentity]]
"""A configured sign-in: reads the request, answers who is calling.

Raises `fastapi.HTTPException` 401 (with whatever challenge headers the
mechanism needs) when nobody is.
"""


class AdminAuth:
    """The library's front door: one instance per service.

    `current_identity` is THE ONE PLACE A PERSON IS ESTABLISHED, and it is a
    single function object held on the instance rather than a method: FastAPI's
    `dependency_overrides` keys on identity, and every `requires(...)` call
    produces a distinct dependency -- the seam the pass builder's management
    UI taught us to keep overridable must therefore be this one, stable
    object.
    """

    def __init__(
        self,
        permission_map: PermissionMap,
        backend: SignInBackend | None = None,
        tenant_parameter: str = "tenant_id",
        tenant_resolver: TenantResolver | None = None,
    ) -> None:
        """Wire the map, the sign-in backend, and how a path names a tenant.

        `tenant_resolver` translates the raw path segment into the tenant key
        permissions carry -- the pass builder's admin routes hold a tenant
        UUID in the path while its permissions name `lmu-ub`. Without one,
        the path value is taken as the key.
        """
        self._map = permission_map
        self._backend = backend
        self._tenant_parameter = tenant_parameter
        self._tenant_resolver = tenant_resolver

        async def current_identity(request: Request) -> AdminIdentity:
            if self._backend is None:
                raise HTTPException(401, "No sign-in backend is configured")
            return await self._backend(request)

        self.current_identity = current_identity

    @classmethod
    def from_settings(
        cls,
        settings: "AdminAuthSettings",
        tenant_parameter: str = "tenant_id",
        tenant_resolver: TenantResolver | None = None,
    ) -> "AdminAuth":
        """Wire the instance a deployment's settings describe.

        Validates the whole permission map up front, so a typo in the vault is
        a startup failure rather than a person quietly lacking a right.
        """
        from .backends.basic import basic_backend
        from .backends.trusted_header import trusted_header_backend

        backend: SignInBackend
        if settings.backend == "trusted_header":
            backend = trusted_header_backend(
                user_header=settings.trusted_user_header,
                groups_header=settings.trusted_groups_header,
                display_name_header=settings.trusted_display_name_header,
                group_separator=settings.trusted_group_separator,
            )
        else:
            backend = basic_backend(settings.basic_users)
        return cls(
            permission_map=PermissionMap.parse(settings.permissions),
            backend=backend,
            tenant_parameter=tenant_parameter,
            tenant_resolver=tenant_resolver,
        )

    def requires(self, permission: str) -> Callable[..., Coroutine[Any, Any, AdminIdentity]]:
        """Return a dependency enforcing ``<object>:<verb>`` in the path's tenant.

        The tenant half of the permission comes from the route, not from this
        argument: the same router is mounted once per estate and serves every
        tenant, so ``requires("templates:write")`` checks
        ``templates:write@<the path's tenant>``.
        """
        # Validated here, at import time of the service module, so a typo is a
        # startup failure rather than a route that refuses everybody.
        _validate_literal(permission, "requires()")

        async def dependency(
            request: Request,
            identity: AdminIdentity = Depends(self.current_identity),  # noqa: B008
        ) -> AdminIdentity:
            return await self._check_identity(request, permission, identity)

        return dependency

    async def check(self, request: Request, permission: str) -> AdminIdentity:
        """Establish the caller and enforce ``<object>:<verb>``, imperatively.

        The twin of `requires()` for host-side seams: a service that declares
        permissions on routes mounted in several applications (consumer,
        in-process UI, admin) cannot hang a dependency needing an identity
        there -- outside the admin mount there is none to resolve. Its seam
        calls this instead, with the same semantics: 401 from the backend,
        400 for a tenant segment the permission form cannot carry, 403 naming
        the missing permission, RuntimeError for a route without a tenant
        segment.
        """
        _validate_literal(permission, "check()")
        identity = await self.current_identity(request)
        return await self._check_identity(request, permission, identity)

    async def _check_identity(
        self, request: Request, permission: str, identity: AdminIdentity
    ) -> AdminIdentity:
        # The permission literal was validated by the entry point (requires()
        # at wiring time, check() before the backend), so this core is about
        # the tenant and the map alone.
        path_value = request.path_params.get(self._tenant_parameter)
        if path_value is None:
            # The route was mounted outside a tenant path. A mistake in
            # the service, not a caller to be refused with 403 -- fail
            # loudly instead of quietly denying everybody.
            raise RuntimeError(
                f"the permission {permission!r} needs a "
                f"{{{self._tenant_parameter}}} path parameter on its route"
            )
        try:
            needed = Permission.parse(f"{permission}@{path_value}")
        except MalformedPermission as error:
            # The segment cannot appear in a permission's tenant half
            # (':' or '@'). A caller's malformed input, checked BEFORE the
            # resolver runs: a resolver that answers a key the form cannot
            # carry stays a server error below, because that key came from
            # our own configuration, not from the caller.
            raise HTTPException(400, "Invalid tenant path segment") from error
        if self._tenant_resolver is not None:
            resolved = self._tenant_resolver(str(path_value))
            tenant = await resolved if inspect.isawaitable(resolved) else resolved
            needed = Permission.parse(f"{permission}@{tenant}")
        if needed not in self._map.resolve(identity.groups):
            raise HTTPException(403, f"Missing permission {needed}")
        return identity


def _validate_literal(permission: str, entry_point: str) -> None:
    """Refuse a permission literal that is not bare ``<object>:<verb>``."""
    try:
        Permission.parse(f"{permission}@-")
    except MalformedPermission as error:
        raise MalformedPermission(
            f"{entry_point} takes <object>:<verb> without a tenant; got {permission!r}"
        ) from error
