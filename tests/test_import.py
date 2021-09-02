import sys


def test_can_import():
    from ansible_collections.release_engineering.pulp2_api.plugins.doc_fragments import (
        base_options,
    )
    from ansible_collections.release_engineering.pulp2_api.plugins.modules import (
        pulp_role,
        pulp_user,
    )
