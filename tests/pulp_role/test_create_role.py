import pytest


def test_create_empty_role(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
    )

    fetch_url.side_effect = [
        # first call: role doesn't exist
        (object(), {"status": 404}),
        # second call: OK, created role
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
        # Then it should do a POST to create the role.
        {
            "data": {
                "role_id": "my-great-role",
                "display_name": "my-great-role",
                "description": "deployed by ansible",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/roles/",
        },
    ]


def test_create_check_mode(
    pulp_role, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        id="my-great-role",
        pulp_url="https://pulp.example.com/pulp",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # role doesn't exist
        (object(), {"status": 404}),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_role.RoleModule().run()

    assert excinfo.value.code == 0

    # It should tell us it wanted to make changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/roles/my-great-role/"},
        # ...and, that's it, since check mode can't really make changes.
    ]


def test_create_with_permissions(
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
        # first call: role doesn't exist
        (object(), {"status": 404}),
        # second call: OK, created role
        (object(), {"status": 200}),
        # third & fourth: OK, granted permissions
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
        # Then it should do a POST to create the role.
        {
            "data": {
                "role_id": "my-great-role",
                "display_name": "my-great-role",
                "description": "deployed by ansible",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/roles/",
        },
        # Then a grant_to_role POST for each of the resources where roles shall be granted.
        {
            "data": {
                "operations": ["CREATE", "UPDATE"],
                "resource": "/path1",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/grant_to_role/",
        },
        {
            "data": {
                "operations": ["EXECUTE", "DELETE"],
                "resource": "/path2",
                "role_id": "my-great-role",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/permissions/actions/grant_to_role/",
        },
    ]
