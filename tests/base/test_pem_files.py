import io
import logging
import os
from unittest import mock

import pytest
from ansible.module_utils import urls
from ansible.module_utils.basic import AnsibleModule


def test_serializes_certs(module_utils_base, set_module_params):
    fake_cert = "-----BEGIN CERTIFICATE-----\nfake\n-----END CERTIFICATE-----\n"
    fake_key = "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n"

    cert_within_module = []
    key_within_module = []

    class MyModule(module_utils_base.BaseModule):
        def __init__(self):
            super().__init__(
                AnsibleModule(
                    dict(client_cert=dict(type=str), client_key=dict(type=str))
                )
            )

        def run_module(self):
            # Inside the module, client_cert/client_key should be put into files.
            # Spy on them to see what we get.
            for key, accum in [
                ("client_cert", cert_within_module),
                ("client_key", key_within_module),
            ]:
                filename = self.module.params[key]
                with open(filename, "rt") as f:
                    content = f.read()
                accum.append((filename, content))

    # Pass cert/key contents as params.
    set_module_params(client_cert=fake_cert, client_key=fake_key)

    # It should run and exit
    with pytest.raises(SystemExit) as excinfo:
        MyModule().run()

    # It should succeed
    assert excinfo.value.code == 0

    for accum, expected_content in [
        (cert_within_module, fake_cert),
        (key_within_module, fake_key),
    ]:
        # It should have seen a cert/key
        assert accum

        (filename, content) = accum[0]

        # The file should no longer exist.
        assert not os.path.exists(filename)

        # While the module was running, it should have existed, with expected content.
        assert content.strip() == expected_content.strip()


def test_no_serialize_other(module_utils_base, set_module_params):
    fake_cert = "some cert string"
    fake_key = "some key string"

    cert_within_module = []
    key_within_module = []

    class MyModule(module_utils_base.BaseModule):
        def __init__(self):
            super().__init__(
                AnsibleModule(
                    dict(client_cert=dict(type=str), client_key=dict(type=str))
                )
            )

        def run_module(self):
            for key, accum in [
                ("client_cert", cert_within_module),
                ("client_key", key_within_module),
            ]:
                accum.append(self.module.params[key])

    # Pass some strings (not valid cert/key) as params.
    set_module_params(client_cert=fake_cert, client_key=fake_key)

    # It should run and exit
    with pytest.raises(SystemExit) as excinfo:
        MyModule().run()

    # It should succeed
    assert excinfo.value.code == 0

    for accum, expected_value in [
        (cert_within_module, fake_cert),
        (key_within_module, fake_key),
    ]:
        # It should have seen a cert/key
        assert accum

        value = accum[0]

        # It should be exactly what was passed in.
        assert value == expected_value
