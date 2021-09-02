#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
---
module: pulp_user
short_description: Manage a user in Pulp 2.x
description:
- Creates, updates or deletes a user in Pulp 2.x.
- Uses Pulp's API.

options:
    login:
        required: true
        type: str
        description:
        - Unique login for the user.
        - 'Example: "test-login".'

    name:
        type: str
        description:
        - Arbitrary user-oriented name for the account.

    password:
        type: str
        description:
        - Password for the account.
        - If unset or blank, the password is not managed.
        - >
            If set, the user account will always be updated, since it is not
            possible for ansible to determine the current password.

    randomize_password:
        type: bool
        default: false
        description:
        - If true, a strong random password will be set.
        - >
            As the password is not logged or known, using this option effectively
            disables password authentication for the account.
        - Conflicts with a non-blank C(password).

    state:
        type: str
        choices:
        - absent
        - present
        description:
        - Defines whether this user should exist.
        default: present

version_added: 0.2.0
author: Rohan McGovern (@rohanpm)
extends_documentation_fragment: release_engineering.pulp2_api.base_options
"""

import secrets

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.release_engineering.pulp2_api.plugins.module_utils.base import (
    COMMON_ARGUMENTS,
    LOG,
    BaseModule,
)


class UserModule(BaseModule):
    def __init__(self):
        super().__init__(
            AnsibleModule(
                argument_spec=dict(
                    login=dict(required=True, type="str"),
                    name=dict(type="str"),
                    password=dict(type="str", default="", no_log=True),
                    randomize_password=dict(type=bool, default=False, no_log=False),
                    state=dict(
                        type="str", default="present", choices=["present", "absent"]
                    ),
                    **COMMON_ARGUMENTS,
                ),
                supports_check_mode=True,
            )
        )

    @property
    def login(self):
        return self.module.params["login"]

    @property
    def name(self):
        return self.module.params.get("name") or self.login

    @property
    def password(self):
        randomize = self.module.params["randomize_password"]
        password = self.module.params["password"]
        if randomize and password:
            self.module.fail_json(
                msg="usage error: cannot set both 'password' and 'randomize_password'"
            )

        if randomize:
            return self.random_password()

        return password or None

    def random_password(self):
        LOG.info("Generating a random password for %s", self.login)
        return secrets.token_urlsafe(64)

    @property
    def user_url(self):
        return f"users/{self.login}/"

    def handle_user_absent(self):
        if self.module.params["state"] == "absent":
            return

        self.changed = True

        if self.module.check_mode:
            return self.exit_ok(msg="would create user (check mode)")

        # When creating a user, we consider a password mandatory, because otherwise
        # Pulp will default it to the literal string "None" (probably unintentional?)
        #
        # If caller asks for a new account and doesn't explicitly set a password, we
        # use a random one to effectively disable password auth.
        password = self.password or self.random_password()

        body = {
            "login": self.login,
            "name": self.name,
            "password": password,
        }

        # Create the user now
        self.update_resource("users/", body)

    def delete_user(self):
        self.changed = True

        if self.module.check_mode:
            return self.exit_ok(msg="would delete user (check mode)")

        self.delete_resource(self.user_url)

    def handle_user_present(self, current_user):
        if self.module.params["state"] == "absent":
            return self.delete_user()

        delta = {}

        if current_user.get("name") != self.name:
            delta["name"] = self.name

        password = self.password
        if password is not None:
            delta["password"] = password

        if delta:
            self.changed = True

            if self.module.check_mode:
                return self.exit_ok(msg="would update user (check mode)")

            # Update it
            self.update_resource(self.user_url, dict(delta=delta), method="PUT")

    def run_module(self):
        current_user = self.get_resource(self.user_url)
        LOG.info("User now: %s", current_user)

        if current_user is None:
            self.handle_user_absent()
        else:
            self.handle_user_present(current_user)

        self.exit_ok()


if __name__ == "__main__":
    UserModule().run()  # pragma: no cover
