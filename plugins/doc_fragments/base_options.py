class ModuleDocFragment:
    DOCUMENTATION = """
description:
- HTTP request behavior can be configured using most of the same options as C(ansible.builtin.uri).

options:
    pulp_url:
        type: str
        required: true
        description:
        - Base URL of the Pulp service.
        - Should include trailing "/pulp/api/v2" component if applicable.
        - 'Example: https://pulp.example.com/pulp/api/v2'

    validate_certs:
        type: bool
        default: true
        description:
        - As for C(ansible.builtin.uri).

    url_username:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    url_password:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    http_agent:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    force_basic_auth:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    follow_redirects:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    client_cert:
        type: str
        description:
        - As for C(ansible.builtin.uri).

    client_key:
        type: str
        description:
        - As for C(ansible.builtin.uri).

seealso:
- module: ansible.builtin.uri
"""
