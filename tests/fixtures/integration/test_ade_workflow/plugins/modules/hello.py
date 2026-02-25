"""A minimal Ansible module for testing tox-ansible workflows."""

from __future__ import annotations


DOCUMENTATION = """
---
module: hello
short_description: A test module
description:
  - Returns a greeting message.
options: {}
"""

RETURN = """
msg:
  description: The greeting message.
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    """Entry point for the module."""
    module = AnsibleModule(argument_spec={})
    module.exit_json(changed=False, msg="Hello from test_ns.test_col")


if __name__ == "__main__":
    main()
