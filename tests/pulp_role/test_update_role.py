import json

import pytest


class Response:
    def __init__(self, **kwargs):
        self._bytes = json.dumps(kwargs).encode("utf8")

    def read(self):
        return self._bytes[:]


def test_update_role(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        permissions={
            "/path1": ["CREATE", "UPDATE"],
            "/path2": ["EXECUTE", "DELETE"],
        },
    )

    fetch_url.side_effect = [
        # first call: role exists but not with desired state
        (
            Response(
                id="my-great-role",
                description="some wrong description",
                display_name="something else",
                permissions={
                    "/path1": ["CREATE"],
                    "/path2": ["CREATE", "EXECUTE"],
                    "/path3": ["UPDATE"],
                },
            ),
            {"status": 200},
        ),
        # second call: update role
        (object(), {"status": 201}),
        # next calls are all granting or revoking permissions
        (object(), {"status": 200}),
        (object(), {"status": 200}),
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
        # Then it should update these fields which didn't match the inputs.
        {
            "data": {
                "delta": {
                    "description": "deployed by ansible",
                    "display_name": "my-great-role",
                }
            },
            "headers": {"Content-Type": "application/json"},
            "method": "PUT",
            "url": "https://pulp.example.com/pulp/roles/my-great-role/",
        },
        # Then revoke ops which shouldn't be there...
        {
            "data": {
                "operations": ["CREATE"],
                "resource": "/path2",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/revoke_from_role/",
        },
        {
            "data": {
                "operations": ["UPDATE"],
                "resource": "/path3",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/revoke_from_role/",
        },
        # And finally grant those which should
        {
            "data": {
                "operations": ["UPDATE"],
                "resource": "/path1",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/grant_to_role/",
        },
        {
            "data": {
                "operations": ["DELETE"],
                "resource": "/path2",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/grant_to_role/",
        },
    ]


def test_update_role_noop(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        description="desc",
        display_name="name",
        permissions={
            "/path1": ["CREATE"],
            "/path2": ["CREATE", "EXECUTE"],
            "/path3": ["UPDATE"],
        },
    )

    fetch_url.side_effect = [
        # first call: role exists and with exactly desired state
        (
            Response(
                id="my-great-role",
                description="desc",
                display_name="name",
                permissions={
                    "/path1": ["CREATE"],
                    "/path2": ["CREATE", "EXECUTE"],
                    "/path3": ["UPDATE"],
                },
            ),
            {"status": 200},
        ),
        # no subsequent calls
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us no changes
    result = out_reader()
    assert not result["changed"]

    assert fetch_url_calls() == [
        # It should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
    ]


def test_update_role_fields_check(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # first call: role exists but not with desired state
        (
            Response(
                id="my-great-role",
                description="some wrong description",
                display_name="something else",
            ),
            {"status": 200},
        ),
        # no subsequent calls due to check mode
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us it would have made changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # Then nothing else - it stopped due to check mode
    ]


def test_update_role_perms_check(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        description="desc",
        display_name="disp",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # first call: role exists but permissions are not in desired state
        (
            Response(
                id="my-great-role",
                description="desc",
                display_name="disp",
                permissions={
                    "/foo": ["BAR", "BAZ"],
                },
            ),
            {"status": 200},
        ),
        # no subsequent calls due to check mode
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us it would have made changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # Then nothing else - it stopped due to check mode
    ]
