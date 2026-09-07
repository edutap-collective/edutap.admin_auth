"""AdminIdentity: who is calling, as the sign-in produced it."""

from edutap.admin_auth.identity import AdminIdentity


def test_carries_subject_display_name_groups_and_raw_claims():
    identity = AdminIdentity(
        subject="jdoe@example.org",
        display_name="J. Doe",
        groups=["ub-admins"],
        claims={"eppn": "jdoe@example.org"},
    )
    assert identity.subject == "jdoe@example.org"
    assert identity.claims["eppn"] == "jdoe@example.org"


def test_claims_default_to_empty():
    identity = AdminIdentity(subject="s", display_name="d", groups=[])
    assert identity.claims == {}
