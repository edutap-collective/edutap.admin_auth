"""Who is calling, as the deployment's sign-in produced it."""

from pydantic import BaseModel, Field


class AdminIdentity(BaseModel):
    """The authenticated person behind an admin request.

    Backends differ in what they can say about a person; this is the shape
    they all agree on. `claims` carries the raw attributes or claims the
    sign-in produced, for the audit trail and for anything a service needs
    beyond the common fields.
    """

    subject: str
    """A stable identifier for the person, e.g. an ePPN or an OIDC `sub`."""

    display_name: str
    """What screens show for this person."""

    groups: list[str]
    """The group or claim values the permission map resolves against."""

    claims: dict[str, object] = Field(default_factory=dict)
    """The raw claims or attributes, untranslated."""
