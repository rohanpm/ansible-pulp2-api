import io

import pytest
from ansible.module_utils import urls
from ansible.module_utils.basic import AnsibleModule


@pytest.mark.parametrize(
    "request_fn",
    [
        (lambda self: self.get_resource("foo/bar")),
        (lambda self: self.update_resource("foo/bar", {"some": "data"})),
        (lambda self: self.delete_resource("foo/bar")),
    ],
    ids=["get", "update", "delete"],
)
def test_http_errors(
    module_utils_base, set_module_params, fetch_url, out_reader, request_fn
):
    class MyModule(module_utils_base.BaseModule):
        def __init__(self):
            super().__init__(AnsibleModule(dict(pulp_url=dict(type=str))))

        def run_module(self):
            request_fn(self)

    set_module_params(pulp_url="https://pulp2.example.com/")

    fetch_url.side_effect = [(io.BytesIO(b"some response data"), {"status": "419"})]

    # It should run and exit
    with pytest.raises(SystemExit) as excinfo:
        MyModule().run()

    # It should have failed
    assert excinfo.value.code != 0

    # It should tell us why
    out = out_reader()
    assert out["failed"]
    assert (
        out["msg"] == "unexpected status 419 from URL https://pulp2.example.com/foo/bar"
    )
