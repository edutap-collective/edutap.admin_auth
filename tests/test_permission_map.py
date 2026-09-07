"""The settings-driven map: group or claim value -> granted permissions."""

import pytest

from edutap.admin_auth.permissions import MalformedPermission, Permission, PermissionMap


def test_resolves_the_union_of_all_matching_groups():
    m = PermissionMap.parse(
        {
            "ub-admins": ["templates:write@lmu-ub", "templates:read@lmu-ub"],
            "auditors": ["audit:read@lmu-ub", "audit:read@lmu"],
        }
    )
    granted = m.resolve(["ub-admins", "auditors"])
    assert granted == {
        Permission.parse("templates:write@lmu-ub"),
        Permission.parse("templates:read@lmu-ub"),
        Permission.parse("audit:read@lmu-ub"),
        Permission.parse("audit:read@lmu"),
    }


def test_a_group_the_map_does_not_know_grants_nothing():
    m = PermissionMap.parse({"ub-admins": ["templates:read@lmu-ub"]})
    assert m.resolve(["strangers"]) == set()


def test_no_groups_grant_nothing():
    m = PermissionMap.parse({"ub-admins": ["templates:read@lmu-ub"]})
    assert m.resolve([]) == set()


def test_rejects_a_malformed_permission_at_parse_time_naming_the_group():
    with pytest.raises(MalformedPermission, match="ub-admins"):
        PermissionMap.parse({"ub-admins": ["templates:write"]})
