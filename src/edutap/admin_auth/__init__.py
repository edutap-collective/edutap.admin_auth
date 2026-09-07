"""Person authentication and per-route permission checks for eduTAP admin APIs."""

from .backends.basic import BasicUser, basic_backend
from .identity import AdminIdentity
from .permissions import MalformedPermission, Permission, PermissionMap
from .requires import AdminAuth, SignInBackend, TenantResolver
from .settings import AdminAuthSettings

__all__ = [
    "AdminAuth",
    "AdminAuthSettings",
    "AdminIdentity",
    "BasicUser",
    "MalformedPermission",
    "Permission",
    "PermissionMap",
    "SignInBackend",
    "TenantResolver",
    "basic_backend",
]
