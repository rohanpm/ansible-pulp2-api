import json
import os
import sys
from unittest import mock

import ansible.module_utils.basic
import pytest

SRCDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True, scope="session")
def collection_in_path(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("pulp2_api_imports")

    os.makedirs(os.path.join(tmpdir, "ansible_collections/release_engineering"))
    os.symlink(
        SRCDIR,
        os.path.join(tmpdir, "ansible_collections/release_engineering/pulp2_api"),
    )
    sys.path.insert(0, str(tmpdir))
    yield


@pytest.fixture(autouse=True)
def fetch_url():
    with mock.patch("ansible.module_utils.urls.fetch_url") as mock_fetch_url:
        # This autouse fixture installs a mock which will simply raise on any call.
        # The idea is to block any real requests by default.
        # Tests need to customize the mock to implement desired behavior.
        mock_fetch_url.side_effect = AssertionError(
            "fetch_url mock called without configuration"
        )
        yield mock_fetch_url


@pytest.fixture
def out_reader(capsys):
    def fn():
        (out, err) = capsys.readouterr()

        # Module should never write anything to stderr
        assert not err

        # Output should be valid JSON
        return json.loads(out)

    return fn


@pytest.fixture
def fetch_url_calls(fetch_url):
    def fn():
        calls = fetch_url.mock_calls
        out = []
        for call in calls:
            kwargs = call.kwargs.copy()
            try:
                kwargs["data"] = json.loads(kwargs["data"])
            except:
                pass
            out.append(kwargs)
        return out

    return fn


@pytest.fixture
def module_utils_base():
    from ansible_collections.release_engineering.pulp2_api.plugins.module_utils import (
        base,
    )

    yield base


@pytest.fixture
def pulp_role():
    from ansible_collections.release_engineering.pulp2_api.plugins.modules import (
        pulp_role,
    )

    yield pulp_role


@pytest.fixture
def pulp_user():
    from ansible_collections.release_engineering.pulp2_api.plugins.modules import (
        pulp_user,
    )

    yield pulp_user


@pytest.fixture(scope="function")
def set_module_params(monkeypatch):
    def fn(**kwargs):
        # ansible caches module inputs here so would share params between
        # modules if not cleared
        setattr(ansible.module_utils.basic, "_ANSIBLE_ARGS", None)

        monkeypatch.setattr(
            sys, "argv", ["", json.dumps(dict(ANSIBLE_MODULE_ARGS=kwargs))]
        )

    return fn
