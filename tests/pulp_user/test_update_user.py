import json
import secrets

import pytest


class Response:
    def __init__(self, **kwargs):
        self._bytes = json.dumps(kwargs).encode("utf8")

    def read(self):
        return self._bytes[:]


def test_update_user(
    pulp_user,
    set_module_params,
    fetch_url,
    fetch_url_calls,
    out_reader,
    monkeypatch,
):
    set_module_params(
        login="my-great-user",
        name="new name",
        randomize_password=True,
        pulp_url="https://pulp.example.com/pulp",
    )

    fetch_url.side_effect = [
        # first call: user exists
        (
            Response(
                login="my-great-user",
                name="my-great-user",
            ),
            {"status": 200},
        ),
        # second call: update user
        (object(), {"status": 201}),
    ]

    monkeypatch.setattr(secrets, "token_urlsafe", lambda _: "abc123")

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
        # Then it should update these fields which didn't match the inputs.
        {
            "data": {
                "delta": {
                    "name": "new name",
                    "password": "abc123",
                }
            },
            "headers": {"Content-Type": "application/json"},
            "method": "PUT",
            "url": "https://pulp.example.com/pulp/users/my-great-user/",
        },
    ]


def test_update_user_noop(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-great-user",
        name="xyz",
        pulp_url="https://pulp.example.com/pulp",
    )

    fetch_url.side_effect = [
        # first call: user exists with correct state
        (
            Response(
                login="my-great-user",
                name="xyz",
            ),
            {"status": 200},
        ),
        # no subsequent calls
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us no changes
    result = out_reader()
    assert not result["changed"]

    assert fetch_url_calls() == [
        # It should try to get the user.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-great-user/"},
    ]


def test_update_user_check(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-great-user",
        pulp_url="https://pulp.example.com/pulp",
        password="abc123",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # first call: user exists
        (
            Response(
                login="my-great-user",
                name="my-great-user",
            ),
            {"status": 200},
        ),
        # no later call due to check mode
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
        # Then nothing, due to check mode.
    ]


def test_update_user_bad_args(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-great-user",
        pulp_url="https://pulp.example.com/pulp",
        password="pwd",
        randomize_password=True,
    )

    fetch_url.side_effect = [
        (object(), {"status": 404}),
    ]

    # It should run, unsuccessfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 1

    # It should tell us the reason for failure
    result = out_reader()
    assert (
        result["msg"]
        == "usage error: cannot set both 'password' and 'randomize_password'"
    )
