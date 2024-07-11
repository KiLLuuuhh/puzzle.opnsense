#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Kilian Soltermann <soltermann@puzzle.ch>, Puzzle ITC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""firewall_alias module: Module to configure opnsense firewall aliases"""

# pylint: disable=duplicate-code
__metaclass__ = type

# https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_documenting.html
# fmt: off
# pylint: disable=duplicate-code
DOCUMENTATION = r'''
---
author:
  - Kilian Soltermann (@killuuuhh)
module: system_settings_logging
short_description: Configure firewall aliases.
version_added: "1.3.0"
description:
  - Module to configure opnsense firewall aliases
options:
  enabled:
    description:
      - If set to True, the Alias will be enabled
      - If set to False, the Alias will not be enabled
    type: bool
    required: false
    default: true
  name:
    description:
      - The name of the alias may only consist of the characters "a-z, A-Z, 0-9 and _"
    type: str
    required: true
  type:
    description:
      - The type used for the Alias
      - Supported types are:
            - hosts (Single hosts by IP or Fully Qualified Domain Name or host exclusions (starts with “!” sign))
            - networks (Entire network p.e. 192.168.1.1/24 or network exclusion eg !192.168.1.0/24)
            - ports (Port numbers or a port range like 20:30)
            - urls (A table of IP addresses that are fetched once)
            - urltables (A table of IP addresses that are fetched on regular intervals.)
            - geoip (Select countries or whole regions)
            - networkgroup (Combine different network type aliases into one)
            - macaddress (MAC address or partial mac addresses like f4:90:ea)
            - bgpasn (Maps autonomous system (AS) numbers to networks where they are responsible for)
            - dynamicipv6host (A Host entry that will auto update on a prefixchange)
            - opnvpngroup (Map user groups to logged in OpenVPN users)
            - internal (Internal aliases which are managed by the product)
            - external (Externally managed alias, this only handles the placeholder. Content is set from another source (plugin, api call, etc))
    type: str
    choices:
        - host
        - networks
        - ports
        - urls
        - urltables
        - geoip
        - networkgroup
        - macaddress
        - bgpasn
        - dynamicipv6host
        - opnvpngroup
        - internal
        - external
    required: true
  content:
    description:
      - Content of the alias
    type: str
    required: true
  statistics:
    description:
      -  Maintain a set of counters for each table entry
    type: bool
    required: false
    default: false
  description:
    description:
      -  Description of the Alias
    type: str
    required: false
  refreshfrequency:
    description:
      -  The frequency that the list will be refreshed, in days + hours, so 1 day and 8 hours means the alias will be refreshed after 32 hours.
    type: int
    required: false
'''

EXAMPLES = r'''
- name: Create an Host Alias with the content 10.0.0.1
  puzzle.opnsense.firewall_alias:
    name: TestAliasTypeHost
    type: host
    statistics: false
    description: Test Alias with type Host
    content: 10.0.0.1

- name: Create a URL Alias with the content www.puzzle.ch
  puzzle.opnsense.firewall_alias:
    name: TestAliasTypeURL
    type: urls
    statistics: false
    description: Test Alias with type URL
    content: www.puzzle.ch
'''

RETURN = '''
opnsense_configure_output:
    description: A List of the executed OPNsense configure function along with their respective stdout, stderr and rc
    returned: always
    type: list
    sample:
      - function: "system_cron_configure"
        params: ["true"]
        rc: 0
        stderr: ""
        stderr_lines: []
        stdout: "Configuring CRON...done."
        stdout_lines: ["Configuring CRON...done."]
      - function: "filter_configure"
        params: []
        rc: 0
        stderr: ""
        stderr_lines: []
        stdout: ""
        stdout_lines: []
'''
# fmt: on
from typing import Optional

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.puzzle.opnsense.plugins.module_utils.firewall_alias_utils import (
    FirewallAlias,
    FirewallAliasSet,
)

ANSIBLE_MANAGED: str = "[ ANSIBLE ]"


def main():
    """Main module execution entry point."""

    module_args = {
        "enabled": {"type": "bool", "required": False, "default": True},
        "name": {"type": "str", "required": True},
        "type": {
            "type": "str",
            "choices": [
                "host",
                "network",
                "port",
                "url",
                "urltables",
                "geoip",
                "networkgroup",
                "macaddress",
                "bgpasn",
                "dynamicipv6host",
                "opnvpngroup",
                "internal",
                "external",
            ],
            "required": True,
        },
        "content": {"type": "str", "required": False},
        "statistics": {"type": "bool", "required": False, "default": False},
        "description": {"type": "str", "required": False},
        "refreshfrequency": {"type": "int", "required": False},
        "state": {"type": "str", "required": False, "default": True},
    }

    module: AnsibleModule = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html
    # https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_documenting.html#return-block
    result = {
        "changed": False,
        "invocation": module.params,
        "diff": None,
    }

    # make description ansible-managed
    description: Optional[str] = module.params["description"]

    if description and ANSIBLE_MANAGED not in description:
        description = f"{ANSIBLE_MANAGED} - {description}"
    else:
        description = ANSIBLE_MANAGED

    module.params["description"] = description

    ansible_alias: FirewallAlias = FirewallAlias.from_ansible_module_params(
        module.params
    )

    ansible_alias_state: str = module.params.get("state")

    with FirewallAliasSet() as alias_set:
        if ansible_alias_state == "present":
            alias_set.add_or_update(ansible_alias)
        else:
            # ansible_rule_state == "absent" since it is the only
            # alternative allowed in the module params
            alias_set.delete(ansible_alias)

        if alias_set.changed:
            result["diff"] = alias_set.diff
            result["changed"] = True
            alias_set.save()
            result["opnsense_configure_output"] = alias_set.apply_settings()
            for cmd_result in result["opnsense_configure_output"]:
                if cmd_result["rc"] != 0:
                    module.fail_json(
                        msg="Apply of the OPNsense settings failed",
                        details=cmd_result,
                    )

    # Return results
    module.exit_json(**result)


if __name__ == "__main__":
    main()