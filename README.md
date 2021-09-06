# Ansible Collection: release_engineering.pulp2_api

An ansible collection for managing Pulp 2.x resources.

[![Build Status](https://github.com/release-engineering/ansible-pulp2-api/actions/workflows/tox.yml/badge.svg)](https://github.com/release-engineering/ansible-pulp2-api/actions/workflows/tox.yml)
[![codecov](https://codecov.io/gh/release-engineering/ansible-pulp2-api/branch/main/graph/badge.svg?token=cAamOYh8p4)](https://codecov.io/gh/release-engineering/ansible-pulp2-api)

<!--TOC-->

- [Ansible Collection: release_engineering.pulp2_api](#ansible-collection-release_engineeringpulp2_api)
  - [Overview](#overview)
  - [Installation](#installation)
  - [Module reference](#module-reference)
    - [Common arguments](#common-arguments)
    - [pulp_user](#pulp_user)
    - [pulp_role](#pulp_role)
  - [Example](#example)
  - [License](#license)

<!--TOC-->

## Overview

This collection includes modules to adjust certain resources within a
[Pulp](https://pulpproject.org/) server. It is compatible with Pulp 2 and
incompatible with Pulp 3.

All operations are performed using HTTP requests to Pulp's API.

## Installation

This collection is not currently published on galaxy.ansible.com.
It may be installed directly from the git repo:

```
ansible-galaxy collection install git+https://github.com/release-engineering/ansible-pulp2-api.git,main
```

If you are using an older version of ansible which does not support installing
from git, you can install from a tarball of the latest stable release:

```
ansible-galaxy collection install https://github.com/release-engineering/ansible-pulp2-api/releases/latest/download/collection.tar.gz
```

## Module reference

Note: this documentation is a summary only. Complete docs may be reviewed using
the `ansible-doc` tool if the collection is installed.

### Common arguments

These arguments are supported by all modules:

| Argument | Notes |
| -------- | ----- |
| pulp_url | Base URL of the Pulp service, including trailing "/pulp/api/v2". |
| validate_certs | As for [ansible.builtin.uri]. |
| url_username | As for [ansible.builtin.uri]. |
| url_password | As for [ansible.builtin.uri]. |
| http_agent | As for [ansible.builtin.uri]. |
| force_basic_auth | As for [ansible.builtin.uri]. |
| follow_redirects | As for [ansible.builtin.uri]. |
| client_cert | As for [ansible.builtin.uri]. |
| client_key | As for [ansible.builtin.uri]. |

### pulp_user

Create, update or delete a Pulp user.

| Argument | Notes |
| -------- | ----- |
| login | Unique login for the user account. |
| state | `absent` or `present`. |
| name | A name for the user. |
| password | Password for the account; if unset or blank, password is not managed. |
| randomize_password | If `True`, a strong random password will be set. |

### pulp_role

Create, update or delete a Pulp role.

| Argument | Notes |
| -------- | ----- |
| id | Unique identifier for the role. |
| state | `absent` or `present`. |
| display_name | Arbitrary human-readable name for the role. |
| description | Arbitrary human-readable description for the role. |
| permissions | A resource => permission mapping associated with the role. |
| users | List of users associated with the role; if omitted, users are not managed. |

## Example

```yaml
- hosts: localhost

  collections:
   - release_engineering.pulp2_api

  tasks:

  # Create accounts for alice & bob.
  - name: Ensure user
    pulp_user:
      pulp_url: "https://pulp.example.com/pulp/api/v2"
      client_cert: pulpadmin.crt
      client_key: pulpadmin.key
      login: "{{ item }}"
    loop: ["bob", "alice"]

  # Ensure alice & bob can manipulate repositories & repo groups.
  - name: Ensure role
    pulp_role:
      pulp_url: "https://pulp.example.com/pulp/api/v2"
      client_cert: pulpadmin.crt
      client_key: pulpadmin.key
      id: repo-manager
      permissions:
         "/v2/repositories": ["CREATE", "UPDATE", "EXECUTE", "DELETE"]
         "/v2/repo_groups": ["CREATE", "UPDATE", "EXECUTE", "DELETE"]
      users: ["bob", "alice"]
```

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

[ansible.builtin.uri]: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/uri_module.html
