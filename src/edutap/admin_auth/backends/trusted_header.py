"""Sign-in by headers a trusted web frontend asserted.

The estate's back-office zone authenticates people at the web frontend
(Shibboleth at the Apache) and asserts the result as request headers; this
backend reads them. It is the pattern the pass builder's management UI
already runs.

**Only ever deploy it behind a frontend that both sets these headers and
strips them from incoming client requests.** Reachable directly, it is not a
sign-in but an open door: any caller could assert any person. That is a
property of the zone, and nothing in this process can verify it.
"""

from fastapi import HTTPException, Request

from ..identity import AdminIdentity
from ..requires import SignInBackend

GROUP_SEPARATOR = ";"
"""How the web frontend joins multi-valued attributes.

Shibboleth's default for `isMemberOf`. A group containing a semicolon would be
indistinguishable from two groups -- that is the frontend's encoding to fix,
not ours to guess around.
"""


def trusted_header_backend(
    user_header: str = "x-remote-user",
    groups_header: str = "x-remote-groups",
    display_name_header: str | None = None,
    group_separator: str = GROUP_SEPARATOR,
) -> SignInBackend:
    """Return a sign-in backend reading the frontend's asserted headers."""

    async def identify(request: Request) -> AdminIdentity:
        subject = request.headers.get(user_header, "").strip()
        if not subject:
            # 401 and not 403: nobody has been identified. Reaching this
            # means the request did not pass through the web frontend --
            # the zone is misconfigured or something is talking to the
            # container directly. No challenge header: there is nothing a
            # client could present that would help.
            raise HTTPException(401, "No authenticated principal was asserted")
        raw_groups = request.headers.get(groups_header, "")
        groups = [part.strip() for part in raw_groups.split(group_separator) if part.strip()]
        display_name = subject
        if display_name_header is not None:
            display_name = request.headers.get(display_name_header, "").strip() or subject
        watched = (user_header, groups_header, display_name_header)
        return AdminIdentity(
            subject=subject,
            display_name=display_name,
            groups=groups,
            claims={
                name: value
                for name in watched
                if name is not None and (value := request.headers.get(name)) is not None
            },
        )

    return identify
