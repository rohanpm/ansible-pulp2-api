import json

import pytest


class Response:
    def __init__(self, **kwargs):
        self._bytes = json.dumps(kwargs).encode("utf8")

    def read(self):
        return self._bytes[:]


def test_delete_noop(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-user", pulp_url="https://pulp.example.com/pulp", state="absent"
    )

    fetch_url.side_effect = [
        # first call: user doesn't exist
        (object(), {"status": 404}),
        # no subsequent calls as nothing to be done
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us no changes
    result = out_reader()
    assert not result["changed"]

    assert fetch_url_calls() == [
        # It should try to get the role.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-user/"},
    ]


def test_delete_existing(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-user",
        pulp_url="https://pulp.example.com/pulp",
        state="absent",
    )

    fetch_url.side_effect = [
        # first call: user exists
        (
            Response(
                login="my-user",
            ),
            {"status": 200},
        ),
        # subsequent call: delete OK
        (object(), {"status": 200}),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us it made changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # It should try to get the user.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-user/"},
        # And then delete it.
        {
            "method": "DELETE",
            "url": "https://pulp.example.com/pulp/users/my-user/",
        },
    ]


def test_delete_check(
    pulp_user, set_module_params, fetch_url, fetch_url_calls, out_reader
):
    set_module_params(
        login="my-user",
        pulp_url="https://pulp.example.com/pulp",
        state="absent",
        _ansible_check_mode=True,
    )

    fetch_url.side_effect = [
        # first call: user exists
        (
            Response(
                login="my-user",
            ),
            {"status": 200},
        ),
    ]

    # It should run, successfully
    with pytest.raises(SystemExit) as excinfo:
        pulp_user.UserModule().run()

    assert excinfo.value.code == 0

    # It should tell us it wanted to make changes
    result = out_reader()
    assert result["changed"]

    assert fetch_url_calls() == [
        # It should try to get the user.
        {"method": "GET", "url": "https://pulp.example.com/pulp/users/my-user/"},
        # But no delete, due to check mode.
    ]
