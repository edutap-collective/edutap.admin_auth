"""The permission form: <object>:<verb>@<tenant>, e.g. templates:write@lmu-ub."""

import pytest

from edutap.admin_auth.permissions import MalformedPermission, Permission


def test_parses_object_verb_and_tenant():
    p = Permission.parse("templates:write@lmu-ub")
    assert p.object == "templates"
    assert p.verb == "write"
    assert p.tenant == "lmu-ub"


def test_renders_back_to_its_string_form():
    assert str(Permission.parse("credentials:read@stwm")) == "credentials:read@stwm"


def test_is_hashable_and_compares_by_value():
    assert Permission.parse("fields:refresh@lmu") in {Permission.parse("fields:refresh@lmu")}


@pytest.mark.parametrize(
    "raw",
    [
        "templates:write",  # no tenant
        "templates@lmu",  # no verb
        "write@lmu",  # no object
        "templates:write@",  # empty tenant
        ":write@lmu",  # empty object
        "templates:@lmu",  # empty verb
        "templates:write@lmu@ub",  # a second @
        "",
    ],
)
def test_rejects_malformed_forms(raw):
    with pytest.raises(MalformedPermission):
        Permission.parse(raw)
