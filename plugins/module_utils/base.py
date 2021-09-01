#!/usr/bin/python3
import contextlib
import json
import logging
import os
from tempfile import NamedTemporaryFile

from ansible.module_utils import urls
from ansible.module_utils.basic import AnsibleModule

LOG = logging.getLogger("release_engineering.pulp2_api")

MODULES = {}

URL_ARGUMENTS = dict(
    # These all come from 'url' module and are understood by module_utils.urls.
    validate_certs=dict(default=True, type="bool"),
    url_username=dict(type="str"),
    url_password=dict(type="str", no_log=True),
    http_agent=dict(type="str", default="ansible-pulp2_api"),
    force_basic_auth=dict(type="str"),
    follow_redirects=dict(type="str"),
    client_cert=dict(type="str"),
    client_key=dict(type="str"),
)

COMMON_ARGUMENTS = dict(
    pulp_url=dict(required=True, type="str"),
    **URL_ARGUMENTS,
)


class BaseModule:
    """A base class for modules in this collection."""

    def __init__(self, module=None):
        self.module = module or AnsibleModule({})
        self.changed = False

    def exit_ok(self, **kwargs):
        changed = kwargs.pop("changed", self.changed)
        return self.module.exit_json(changed=changed, **kwargs)

    def api_url(self, rest):
        return os.path.join(self.module.params["pulp_url"], rest)

    def get_resource(self, rest):
        url = self.api_url(rest)
        LOG.info("Fetching %s", url)

        (response, info) = urls.fetch_url(self.module, url=url, method="GET")

        status_code = info["status"]

        if status_code == 404:
            LOG.info("%s => resource doesn't exist", url)
            return None

        if status_code == 200:
            data = json.load(response)
            LOG.info("%s => %s", url, data)
            return data

        raw_data = response.read() if response else "<no response object>"
        LOG.warning("Unexpected response: %s, %s", info, raw_data)

        self.module.fail_json(msg=f"unexpected status {status_code} from URL {url}")

    def update_resource(self, rest, body, method="POST"):
        url = self.api_url(rest)
        LOG.info("%s %s", method, url)

        body_json = json.dumps(body)

        (response, info) = urls.fetch_url(
            self.module,
            url=url,
            method=method,
            data=body_json,
            headers={"Content-Type": "application/json"},
        )

        status_code = info["status"]
        LOG.info("%s => %s", url, status_code)

        if status_code in (201, 200):
            return

        raw_data = response.read() if response else "<no response object>"
        LOG.warning("Unexpected response: %s, %s", info, raw_data)

        self.module.fail_json(msg=f"unexpected status {status_code} from URL {url}")

    def delete_resource(self, rest):
        url = self.api_url(rest)
        LOG.info("DELETE %s", url)

        (response, info) = urls.fetch_url(
            self.module,
            url=url,
            method="DELETE",
        )

        status_code = info["status"]
        LOG.info("%s => %s", url, status_code)

        if status_code in (200, 404):
            return

        raw_data = response.read() if response else "<no response object>"
        LOG.warning("Unexpected response: %s, %s", info, raw_data)

        self.module.fail_json(msg=f"unexpected status {status_code} from URL {url}")

    def run(self):
        if os.environ.get("PULP2_API_LOG"):
            logging.basicConfig(
                level=logging.INFO, filename=os.environ["PULP2_API_LOG"]
            )

        with self.pem_files():
            self.run_module()

        # run_module can exit early if it wants. If it completes without exiting
        # or raising, we take it as a success.
        self.exit_ok()

    def run_module(self):
        raise NotImplementedError()

    @contextlib.contextmanager
    def pem_files(self):
        # A context manager to convert 'client_cert', 'client_key' parameters
        # from PEM-formatted strings into paths to files containing PEM-formatted
        # strings.
        #
        # Why: module_utils.urls expects *path to cert/key*, not *cert/key*.
        # However, it also won't unvault anything vaulted, so you can't pass it
        # a path to a vaulted key. Where are you meant to unvault then?
        #
        # This module's answer is that you can e.g. use a lookup('file', ...) first
        # which will unvault, but then we need to put the content back into a file
        # before we can call module_utils.urls ...
        #
        # This seems badly designed and more complicated than it should be, maybe
        # I'm missing something here?
        #
        files = []
        old_params = {}

        for param in ("client_cert", "client_key"):
            if not self.module.params.get(param):
                continue

            value = self.module.params[param]
            if "-----BEGIN" not in value:
                continue

            tempfile = NamedTemporaryFile(suffix="pulp2_api")
            tempfile.write(value.encode("utf8") + b"\n")
            tempfile.flush()
            files.append(tempfile)

            LOG.debug("%s serialized to %s", param, tempfile.name)

            old_params[param] = self.module.params[param]
            self.module.params[param] = tempfile.name

        try:
            yield
        finally:
            self.module.params.update(old_params)
            for file in files:
                file.close()
