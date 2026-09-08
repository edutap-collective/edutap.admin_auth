"""Configuration, from the environment -- the vault, the deploy diff."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .backends.basic import BasicUser
from .backends.trusted_header import GROUP_SEPARATOR


class AdminAuthSettings(BaseSettings):
    """What a deployment decides: the sign-in, the users (basic), the map."""

    model_config = SettingsConfigDict(env_prefix="EDUTAP_ADMIN_AUTH_")

    backend: Literal["basic", "trusted_header"]
    """Which sign-in guards the admin API.

    No default: the choice is a deployment decision, and a default would make
    it an accident. `saml` and `oidc` need a wired SP/RP instance and are
    therefore passed to `AdminAuth` directly (via `federated_backend`) rather
    than named here.
    """

    permissions: dict[str, list[str]] = Field(default_factory=dict)
    """Group or claim value -> permission strings (``object:verb@tenant``)."""

    basic_users: dict[str, BasicUser] = Field(default_factory=dict)
    """The user table for the `basic` backend; ignored by every other."""

    trusted_user_header: str = "x-remote-user"
    """`trusted_header` backend: where the frontend asserts the person."""

    trusted_groups_header: str = "x-remote-groups"
    """`trusted_header` backend: where the frontend asserts the groups."""

    trusted_display_name_header: str | None = None
    """`trusted_header` backend: where a display name is asserted, if anywhere."""

    trusted_group_separator: str = GROUP_SEPARATOR
    """`trusted_header` backend: how the frontend joins multiple groups."""
