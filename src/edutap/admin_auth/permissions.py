"""The permission vocabulary: ``<object>:<verb>@<tenant>``.

The tenant is inside the permission rather than a field beside it: the estate
runs several tenants under different bodies, and the same person routinely
holds different rights in each. A permission that does not carry the tenant
cannot say so.
"""

import re
from dataclasses import dataclass

_FORM = re.compile(r"^(?P<object>[^:@]+):(?P<verb>[^:@]+)@(?P<tenant>[^:@]+)$")


class MalformedPermission(ValueError):
    """A string that does not read as ``<object>:<verb>@<tenant>``."""


@dataclass(frozen=True)
class Permission:
    """One granted or required right, tenant included."""

    object: str
    verb: str
    tenant: str

    @classmethod
    def parse(cls, raw: str) -> "Permission":
        """Parse ``templates:write@lmu-ub`` into its three parts."""
        match = _FORM.match(raw)
        if match is None:
            raise MalformedPermission(f"{raw!r} does not read as <object>:<verb>@<tenant>")
        return cls(**match.groupdict())

    def __str__(self) -> str:
        """Render the canonical string form."""
        return f"{self.object}:{self.verb}@{self.tenant}"


@dataclass(frozen=True)
class PermissionMap:
    """Group or claim value -> granted permissions, straight from settings.

    Deliberately not a user store: the map lives in the deployment's settings
    (the vault, the deploy diff), so removing a person is a group change in
    the identity provider or one diff here -- never an N-step job across
    services.
    """

    grants: tuple[tuple[str, frozenset[Permission]], ...]

    @classmethod
    def parse(cls, raw: dict[str, list[str]]) -> "PermissionMap":
        """Validate every permission string up front, naming the group at fault."""
        grants = []
        for group, permissions in raw.items():
            try:
                parsed = frozenset(Permission.parse(p) for p in permissions)
            except MalformedPermission as error:
                raise MalformedPermission(f"group {group!r}: {error}") from error
            grants.append((group, parsed))
        return cls(grants=tuple(grants))

    def resolve(self, groups: list[str]) -> set[Permission]:
        """Return the union of everything the given groups grant."""
        wanted = set(groups)
        granted: set[Permission] = set()
        for group, permissions in self.grants:
            if group in wanted:
                granted |= permissions
        return granted
