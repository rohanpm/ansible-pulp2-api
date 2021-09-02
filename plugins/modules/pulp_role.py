#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
---
module: pulp_role
short_description: Manage a role in Pulp 2.x
description:
- Creates, updates or deletes a role (for role-based access control) in Pulp 2.x.
- Uses Pulp's API.

options:
    id:
        required: true
        type: str
        description:
        - Unique identifier for the role.
        - 'Example: "super-users".'

    display_name:
        type: str
        description:
        - Arbitrary user-oriented name for the role.

    description:
        type: str
        description:
        - A brief description of this role.

    state:
        type: str
        choices:
        - absent
        - present
        description:
        - Defines whether this role should exist.
        default: present

    permissions:
        type: dict
        description:
        - A resource => permission mapping associated with the role.
        - 'Example: C({"/": ["READ"], "/v2/repositories": ["CREATE", "UPDATE"]})'
        default: '{}'

    users:
        type: list
        elements: str
        description:
        - List of all users associated with this role.
        - If omitted, users per role will not be managed.
        - 'Example: C(["bob", "alice"])'
        version_added: 0.3.0

version_added: 0.1.0
author: Rohan McGovern (@rohanpm)
extends_documentation_fragment: release_engineering.pulp2_api.base_options
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.release_engineering.pulp2_api.plugins.module_utils.base import (
    COMMON_ARGUMENTS,
    LOG,
    BaseModule,
)


class RoleModule(BaseModule):
    def __init__(self):
        super().__init__(
            AnsibleModule(
                argument_spec=dict(
                    id=dict(required=True, type="str"),
                    display_name=dict(type="str"),
                    description=dict(type="str", default="deployed by ansible"),
                    permissions=dict(type=dict, default={}),
                    users=dict(type=list, default=None),
                    state=dict(
                        type="str", default="present", choices=["present", "absent"]
                    ),
                    **COMMON_ARGUMENTS,
                ),
                supports_check_mode=True,
            )
        )

    @property
    def role_id(self):
        return self.module.params["id"]

    @property
    def role_url(self):
        return f"roles/{self.role_id}/"

    @property
    def role_users(self):
        return self.module.params.get("users")

    @property
    def display_name(self):
        return self.module.params["display_name"] or self.role_id

    @property
    def description(self):
        return self.module.params["description"]

    def adjust_permissions(self, current_role):
        current_perm = current_role.get("permissions") or {}
        desired = self.module.params["permissions"]

        LOG.debug("current perm %s, desired %s", current_perm, desired)

        # Gather what we need to grant and revoke.
        to_revoke = {}
        to_grant = {}

        for resource_path, ops in current_perm.items():
            desired_ops = desired.get(resource_path) or []
            for op in ops:
                if op not in desired_ops:
                    to_revoke.setdefault(resource_path, []).append(op)

        for resource_path, ops in desired.items():
            current_ops = current_perm.get(resource_path) or []
            for op in ops:
                if op not in current_ops:
                    to_grant.setdefault(resource_path, []).append(op)

        if not to_revoke and not to_grant:
            return

        self.changed = True

        if (to_revoke or to_grant) and self.module.check_mode:
            return self.exit_ok(
                msg="would adjust permissions (check mode)",
            )

        for (actions, action_type) in [
            (to_revoke, "revoke_from_role"),
            (to_grant, "grant_to_role"),
        ]:
            path = f"permissions/actions/{action_type}/"

            for resource in sorted(actions.keys()):
                ops = actions[resource]
                body = dict(role_id=self.role_id, resource=resource, operations=ops)
                LOG.debug("%s %s %s", action_type, resource, ops)
                self.update_resource(path, body)

    def adjust_users(self, current_role):
        current_users = current_role.get("users") or []
        desired = self.role_users

        LOG.debug("current users %s, desired %s", current_users, desired)

        if desired is None:
            # Don't manage users in this case
            return

        # Gather who we need to add and remove.
        to_remove = set()
        to_add = set()

        for username in current_users:
            if username not in desired:
                to_remove.add(username)

        for username in desired:
            if username not in current_users:
                to_add.add(username)

        if not to_remove and not to_add:
            return

        self.changed = True

        if (to_remove or to_add) and self.module.check_mode:
            return self.exit_ok(msg="would adjust users (check mode)")

        for username in sorted(to_remove):
            self.delete_resource(f"{self.role_url}users/{username}/")

        for username in sorted(to_add):
            self.update_resource(f"{self.role_url}users/", {"login": username})

    def handle_role_absent(self):
        if self.module.params["state"] == "absent":
            return

        self.changed = True

        if self.module.check_mode:
            return self.exit_ok(msg="would create role (check mode)")

        # Create the role now
        self.update_resource(
            "roles/",
            {
                "role_id": self.role_id,
                "display_name": self.display_name,
                "description": self.description,
            },
        )

        # If we've just created a role, there are no permissions or users yet.
        # Adjust them as needed.
        current_role = {"permissions": {}, "users": []}
        self.adjust_permissions(current_role)
        self.adjust_users(current_role)

    def delete_role(self):
        self.changed = True

        if self.module.check_mode:
            return self.exit_ok(msg="would delete role (check mode)")

        self.delete_resource(self.role_url)

    def handle_role_present(self, current_role):
        if self.module.params["state"] == "absent":
            return self.delete_role()

        delta = {}

        if current_role.get("display_name") != self.display_name:
            delta["display_name"] = self.display_name
        if current_role.get("description") != self.description:
            delta["description"] = self.description

        if delta:
            self.changed = True

            if self.module.check_mode:
                return self.exit_ok(msg="would update role (check mode)")

            # Update it
            self.update_resource(
                f"roles/{self.role_id}/", dict(delta=delta), method="PUT"
            )

        self.adjust_permissions(current_role)
        self.adjust_users(current_role)

    def run_module(self):
        current_role = self.get_resource(self.role_url)
        LOG.info("Role now: %s", current_role)

        if current_role is None:
            self.handle_role_absent()
        else:
            self.handle_role_present(current_role)

        self.exit_ok()


if __name__ == "__main__":
    RoleModule().run()  # pragma: no cover
