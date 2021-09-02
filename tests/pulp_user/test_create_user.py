import secrets

import pytest


def test_create_user(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader, monkeypatch
):
    set_module_params(
        login="my-great-user",
        pulp_url="https://pulp.example.com/pulp",
    )

    fetch_url.side_effect = [
        # first call: user doesn't exist
        (object(), {"status": 404}),
        # second call: OK, created user
        (object(), {"status": 200}),
    ]

    monkeypatch.setattr(secrets, "token_urlsafe", lambda _: "super-strong-password")

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us it made changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the user.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-great-user/"},
        # Then it should do a POST to create the user.
        {
            "data": {
                "login": "my-great-user",
                "name": "my-great-user",
                "password": "super-strong-password",
            },
            "headers": {"Content-Type": "application/json"},
            "method": "POST",
            "url": "https://pulp.example.com/pulp/users/",
        },
    ]


def test_create_check_mode(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-great-user",
        pulp_url="https://pulp.example.com/pulp",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # user doesn't exist
        (object(), {"status": 404}),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us it wanted to make changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # First it should try to get the user.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-great-user/"},
        # ...and, that's it, since check mode can't really make changes.
    ]
