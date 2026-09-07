"""Configuration, from the environment -- the vault, the deploy diff."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .backends.basic import BasicUser


class AdminAuthSettings(BaseSettings):
    """What a deployment decides: the sign-in, the users (basic), the map."""

    model_config = SettingsConfigDict(env_prefix="EDUTAP_ADMIN_AUTH_")

    backend: Literal["basic"]
    """Which sign-in guards the admin API.

    No default: the choice is a deployment decision, and a default would make
    it an accident. `saml` and `oidc` join this literal when their wrappers
    land.
    """

    permissions: dict[str, list[str]] = Field(default_factory=dict)
    """Group or claim value -> permission strings (``object:verb@tenant``)."""

    basic_users: dict[str, BasicUser] = Field(default_factory=dict)
    """The user table for the `basic` backend; ignored by every other."""
