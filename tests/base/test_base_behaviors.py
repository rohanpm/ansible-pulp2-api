import io
import logging
import os
from unittest import mock

import pytest
from ansible.module_utils import urls
from ansible.module_utils.basic import AnsibleModule


def test_enables_logs(module_utils_base, set_module_params, monkeypatch):
    class MyModule(module_utils_base.BaseModule):
        def __init__(self):
            super().__init__(AnsibleModule(dict()))

        def run_module(self):
            pass

    set_module_params()

    monkeypatch.setenv("PULP2_API_LOG", "/some/log/file")

    # It should run and exit
    with pytest.raises(SystemExit) as excinfo:
        with mock.patch("logging.basicConfig") as mock_basicConfig:
            MyModule().run()

    # It should succeed
    assert excinfo.value.code == 0

    # It should have configured loggers
    mock_basicConfig.assert_called_once_with(
        level=logging.INFO, filename="/some/log/file"
    )


def test_is_abc(module_utils_base):
    module = module_utils_base.BaseModule()

    with pytest.raises(NotImplementedError):
        module.run()
