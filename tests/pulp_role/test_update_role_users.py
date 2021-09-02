import json

import pytest


class Response:
    def __init__(self, **kwargs):
        self._bytes = json.dumps(kwargs).encode("utf8")

    def read(self):
        return self._bytes[:]


def test_update_role_users(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        users=["user1", "user2"],
    )

    fetch_url.side_effect = [
        # first call: role exists but not with desired state (users)
        (
            Response(
                id="my-great-role",
                description="deployed by ansible",
                display_name="my-great-role",
                permissions={},
                users=["user1", "other-user"],
            ),
            {"status": 200},
        ),
        # next calls are all adding or removing users from role
        (object(), {"status": 200}),
        (object(), {"status": 200}),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us it made changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # Then it should remove the user which shouldn't be there
        {
            "method": "DELETE",
            "url": "https://pulp.example.com/pulp/roles/my-great-role/users/other-user/",
        },
        # And add the user which should be there
        {
            "data": {
                "login": "user2",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/roles/my-great-role/users/",
        },
    ]


def test_update_role_users_noop(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        users=["user1", "user2"],
    )

    fetch_url.side_effect = [
        # first call: role exists, with desired state (users)
        (
            Response(
                id="my-great-role",
                description="deployed by ansible",
                display_name="my-great-role",
                permissions={},
                users=["user2", "user1"],
            ),
            {"status": 200},
        ),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us no changes needed
    result = out_reader()
    assert not result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # ...and that's all
    ]


def test_update_role_users_check(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        users=["user1", "user2", "user3"],
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # first call: role exists, with undesired state
        (
            Response(
                id="my-great-role",
                description="deployed by ansible",
                display_name="my-great-role",
                permissions={},
                users=["user2", "user1"],
            ),
            {"status": 200},
        ),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us changes are desired
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # ...and that's all, since we're in check mode
    ]
