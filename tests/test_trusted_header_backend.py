"""The trusted-header sign-in: a person asserted by the zone's web frontend."""

import pytest
from fastapi import HTTPException, Request

from edutap.admin_auth.backends.trusted_header import trusted_header_backend


def request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )


async def test_reads_subject_and_semicolon_separated_groups():
    backend = trusted_header_backend()
    admin = await backend(request({"x-remote-user": "jdoe@lmu.de", "x-remote-groups": "a; b;; c "}))
    assert admin.subject == "jdoe@lmu.de"
    assert admin.groups == ["a", "b", "c"]


async def test_no_asserted_user_is_a_401():
    # Nobody has been identified: the request did not pass through the web
    # frontend -- the zone is misconfigured or something talks to the
    # container directly.
    with pytest.raises(HTTPException) as error:
        await trusted_header_backend()(request({}))
    assert error.value.status_code == 401


async def test_a_blank_asserted_user_is_a_401_too():
    with pytest.raises(HTTPException) as error:
        await trusted_header_backend()(request({"x-remote-user": "   "}))
    assert error.value.status_code == 401


async def test_missing_groups_header_means_no_groups_not_an_error():
    admin = await trusted_header_backend()(request({"x-remote-user": "jdoe"}))
    assert admin.groups == []


async def test_header_names_and_separator_are_configurable():
    backend = trusted_header_backend(
        user_header="x-shib-eppn",
        groups_header="x-shib-ismemberof",
        group_separator=",",
    )
    admin = await backend(request({"x-shib-eppn": "jdoe", "x-shib-ismemberof": "a,b"}))
    assert admin.groups == ["a", "b"]


async def test_display_name_comes_from_its_header_and_falls_back_to_subject():
    named = await trusted_header_backend(display_name_header="x-display-name")(
        request({"x-remote-user": "jdoe", "x-display-name": "J. Doe"})
    )
    assert named.display_name == "J. Doe"
    bare = await trusted_header_backend(display_name_header="x-display-name")(
        request({"x-remote-user": "jdoe"})
    )
    assert bare.display_name == "jdoe"


async def test_the_raw_header_values_reach_the_claims():
    admin = await trusted_header_backend()(
        request({"x-remote-user": "jdoe", "x-remote-groups": "a;b"})
    )
    assert admin.claims == {"x-remote-user": "jdoe", "x-remote-groups": "a;b"}
