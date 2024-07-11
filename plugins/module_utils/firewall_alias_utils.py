#  Copyright: (c) 2024, Puzzle ITC, Kilian Soltermann <soltermann@puzzle.ch>
#  GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Utilities for alias related operations.
"""
import uuid
import re
import ipaddress
from typing import List, Optional

from xml.etree.ElementTree import Element, ElementTree
from ansible_collections.puzzle.opnsense.plugins.module_utils import xml_utils
from ansible_collections.puzzle.opnsense.plugins.module_utils.config_utils import (
    OPNsenseModuleConfig,
)
from ansible_collections.puzzle.opnsense.plugins.module_utils.system_access_users_utils import (
    Group,
)
from ansible_collections.puzzle.opnsense.plugins.module_utils.interfaces_assignments_utils import (
    InterfaceAssignment,
)
from ansible_collections.puzzle.opnsense.plugins.module_utils.enum_utils import ListEnum


class OPNsenseContentValidationError(Exception):
    """
    Exception raised when the validation of a specific value does not succeed
    """


class OPNsenseInterfaceNotFoundError(Exception):
    """
    Exception raised if the defined interface is not found on the device
    """


class IPProtocol(ListEnum):
    """Represents the IPProtocol."""

    IPv4 = "IPv4"
    IPv6 = "IPv6"


class FirewallAliasType(ListEnum):
    """
    some docstring
    """

    HOSTS = "host"
    NETWORKS = "network"
    PORTS = "port"
    URLS = "url"
    URLTABLES = "urltable"
    GEOIP = "geoip"
    NETWORKGROUP = "networkgroup"
    MACADDRESS = "mac"
    BGPASN = "bgpasn"
    DYNAMICIPV6HOST = "dynipv6host"
    OPNVPNGROUP = "opnvpngroup"
    INTERNAL = "internal"
    EXTERNAL = "external"


class FirewallAlias:
    """
    some docstring
    """

    def __init__(self, **kwargs):

        # set default attributes
        self.uuid: Optional[str] = kwargs.get("uuid", str(uuid.uuid4()))
        self.enabled: bool = True
        self.proto: Optional[IPProtocol] = None
        self.counters: Optional[bool] = False
        self.interface: Optional[str] = None
        self.updatefreq: Optional[int] = None
        self.content: Optional[List[str]] = []
        self.name = kwargs.get("name", None)
        self.type: Optional[FirewallAliasType] = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.__post_init__()

    def __post_init__(self):
        # Manually define the fields and their expected types
        enum_fields = {"type": FirewallAliasType}

        for field_name, field_type in enum_fields.items():
            value = getattr(self, field_name)

            # Check if the value is a string and the field_type is a subclass of ListEnum
            if isinstance(value, str) and issubclass(field_type, ListEnum):

                # Convert string to ListEnum
                setattr(self, field_name, field_type.from_string(value))

    def __eq__(self, other):
        if isinstance(other, FirewallAlias):
            return self.__dict__ == other.__dict__
        return False

    @staticmethod
    def from_xml(element: Element) -> "FirewallAlias":
        """
        some docstring
        """

        firewall_alias_dict: dict = xml_utils.etree_to_dict(element)["alias"]

        # get uuid tag
        firewall_alias_dict.update(
            uuid=element.attrib.get("uuid"),
            enabled=firewall_alias_dict.get("enabled", "0") == "1",
            counters=firewall_alias_dict.get("counters", "0") == "1",
        )

        if isinstance(firewall_alias_dict.get("content"), str):
            firewall_alias_dict["content"] = [
                line.strip()
                for line in firewall_alias_dict["content"].splitlines()
                if line.strip()
            ]

        # process attribute content to a list
        elif isinstance(firewall_alias_dict.get("content"), list):
            firewall_alias_dict["content"] = [
                line.strip()
                for line in firewall_alias_dict["content"].splitlines()
                if line.strip()
            ]

        return FirewallAlias(**firewall_alias_dict)

    @classmethod
    def from_ansible_module_params(cls, params: dict) -> "FirewallAlias":
        """
        some docstring
        """
        if params.get("type") == "macaddress":
            params["type"] = "mac"

        if params.get("type") == "dynamicipv6host":
            params["type"] = "dynipv6host"

        firewall_alias_dict: dict = {
            "enabled": params.get("enabled"),
            "name": params.get("name"),
            "type": params.get("type"),
            "content": params.get("content"),
            "counters": params.get("statistics"),
            "interface": (
                params.get("interface") if params.get("type") == "dynipv6host" else None
            ),
            "description": params.get("description"),
            "updatefreq": params.get("refreshfrequency"),
        }

        firewall_alias_dict = {
            key: value
            for key, value in firewall_alias_dict.items()
            if value is not None
        }

        return cls(**firewall_alias_dict)

    def to_etree(self) -> Element:
        """
        some docstring
        """

        firewall_alias_dict: dict = self.__dict__.copy()
        del firewall_alias_dict["uuid"]

        for alias_key, alias_val in firewall_alias_dict.copy().items():

            if alias_key in ["enabled", "counters"]:
                firewall_alias_dict[alias_key] = "0" if alias_val is False else "1"
                continue

            if isinstance(alias_val, bool):
                firewall_alias_dict[alias_key] = "0" if alias_val is False else "1"
                continue

            if issubclass(type(alias_val), ListEnum):
                firewall_alias_dict[alias_key] = alias_val.value
                continue

        # Handle content field if it is a list
        if isinstance(firewall_alias_dict.get("content"), list):
            firewall_alias_dict["content"] = (
                "\n"
                + "\n".join([f"{item}" for item in firewall_alias_dict["content"]])
                + "\n"
            )

        element: Element = xml_utils.dict_to_etree("alias", firewall_alias_dict)[0]

        if self.uuid:
            element.attrib["uuid"] = self.uuid

        return element


class FirewallAliasSet(OPNsenseModuleConfig):
    """
    some docstring
    """

    _aliases: List[FirewallAlias]

    def __init__(self, path: str = "/conf/config.xml"):
        super().__init__(
            module_name="firewall_alias",
            config_context_names=[
                "firewall_alias",
                "system_access_users",
                "interfaces_assignments",
            ],
            path=path,
        )
        self._aliases = self._load_aliases()

    def _load_aliases(self) -> List[FirewallAlias]:
        """
        some doctring
        """

        element_tree_alias: Element = self.get("alias")

        return [FirewallAlias.from_xml(element) for element in element_tree_alias]

    @staticmethod
    def is_hostname_ip_or_range(host: str) -> bool:
        """
        Validates if the entry is a hostname, an IP address, or an IP range.

        :param entry: A string containing the entry

        :return: True if the provided entry is valid, False if it's invalid
        """

        hostname_regex = (
            r"^!?(?:(?:[a-zA-Z0-9_]|[a-zA-Z0-9_][a-zA-Z0-9_\-]"
            r"*[a-zA-Z0-9_])\.)*(?:[a-zA-Z0-9_]|[a-zA-Z0-9_][a-zA-Z0-9_\-]*[a-zA-Z0-9_])$"
        )

        if re.match(hostname_regex, host):
            return True

        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_network(network: str) -> bool:
        """
        Validates network addresses (including optional '!' at the beginning).

        :param network: A string containing the network address.

        :return: True if the provided network address is valid, False if it's invalid.
        """
        if network.startswith("!"):
            network = network[1:]
        try:
            ipaddress.ip_network(network, strict=False)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_port(port: str) -> bool:
        """
        Validates port numbers (including optional '!' at the beginning).

        :param port: A string containing the port number.

        :return: True if the provided port number is valid, False if it's invalid.
        """
        port_regex = (
            r"^(?!.*!)([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
            r"|^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]):([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
        )

        return re.match(port_regex, port) is not None

    @staticmethod
    def is_macaddress(macaddress: str) -> bool:
        """
        Validates MAC addresses (including optional '!' at the beginning).

        :param macaddress: A string containing the MAC address.

        :return: True if the provided MAC address is valid, False if it's invalid.
        """
        macaddress_regex = r"^!?([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$"
        return re.match(macaddress_regex, macaddress) is not None

    @staticmethod
    def is_bgpasn(bgpasn: str) -> bool:
        """
        Validates BGP Autonomous System Numbers (including optional '!' at the beginning).

        :param bgpasn: A string containing the BGP ASN.

        :return: True if the provided BGP ASN is valid, False if it's invalid.
        """
        bgpasn_regex = r"^!?([1-9][0-9]{0,4}|[1-3][0-9]{5}|4[0-2][0-9]{4}|43[0-1][0-9]{3}|432[0-6][0-9]{2}|4327[0-6][0-9]|43277[0-5])$"
        return re.match(bgpasn_regex, bgpasn) is not None

    def is_dynamicipv6host(ipv6_address: str) -> bool:
        """
        Validates IPv6 addresses for dynamic IPv6 hosts.

        :param ipv6_address: A string containing the IPv6 address.

        :return: True if the provided IPv6 address is valid for dynamic IPv6 hosts, False if it's invalid.
        """
        ipv6_regex = r"^::([0-9a-fA-F]{1,4}:){0,3}[0-9a-fA-F]{1,4}$"
        return re.match(ipv6_regex, ipv6_address) is not None

    def is_networkgroup(self, type_network_alias: str) -> bool:
        """
        some docstring
        """

        existing_alias: Optional[FirewallAlias] = next(
            (
                a
                for a in self._aliases
                if a.name == type_network_alias
                and a.type.value in {"network", "networkgroup", "internal"}
            ),
            None,
        )

        return existing_alias is not None

    def is_opnvpngroup(self, type_opnvpngroup_alias: str) -> bool:
        """
        some docstring
        """

        # load groups
        element_tree_groups: Element = self.get("system")

        element_tree_groups.findall("group")

        group_list = []
        for group in element_tree_groups:
            if group.tag == "group":
                group_list.append(Group.from_xml(group))

        existing_group: Optional[Group] = next(
            (g for g in group_list if g.name == type_opnvpngroup_alias),
            None,
        )

        return existing_group is not None

    def is_interface(self, interface_name: str) -> bool:
        """
        some docstring
        """

        element_tree_interfaces: Element = self.get("interfaces")

        interfaces_list: List = []
        for interface in element_tree_interfaces:
            interfaces_list.append(InterfaceAssignment.from_xml(interface))

        existing_interface: Optional[Group] = next(
            (i for i in interfaces_list if i.descr == interface_name),
            None,
        )

        if not existing_interface:
            raise OPNsenseInterfaceNotFoundError(
                f"interface {interface_name} was not found on the device"
            )

        return existing_interface

    def validate_content(
        self, content_type: FirewallAliasType, content_values: List[str]
    ) -> bool:
        """
        some docstring
        """

        content_type_map = {
            "host": {
                "validation_function": FirewallAliasSet.is_hostname_ip_or_range,
                "error_message": "Entry {entry} is not a valid hostname, IP address or range.",
            },
            "network": {
                "validation_function": FirewallAliasSet.is_network,
                "error_message": "Entry {entry} is not a network.",
            },
            "networkgroup": {
                "validation_function": self.is_networkgroup,
                "error_message": "Entry {entry} is not a type NetworkAlias or InternalAlias.",
            },
            "port": {
                "validation_function": FirewallAliasSet.is_port,
                "error_message": "Entry {entry} is not a valid port number.",
            },
            "mac": {
                "validation_function": FirewallAliasSet.is_macaddress,
                "error_message": "Entry {entry} is not a valid (partial) MAC address.",
            },
            "bgpasn": {
                "validation_function": FirewallAliasSet.is_bgpasn,
                "error_message": "Entry {entry} is not a valid ASN.",
            },
            "dynipv6host": {
                "validation_function": FirewallAliasSet.is_dynamicipv6host,
                "error_message": "Entry {entry} is not a valid partial IPv6 address definition (e.g. ::1000).",
            },
            "opnvpngroup": {
                "validation_function": self.is_opnvpngroup,
                "error_message": "Group {entry} was not found on the Instance.",
            },
        }

        for content_value in content_values:

            # since not all types need validation, unhandled types are ingnored
            if not content_type_map.get(content_type.value):
                return True

            validation_function = content_type_map[content_type.value].get(
                "validation_function"
            )

            if not validation_function(content_value):

                raise OPNsenseContentValidationError(
                    content_type_map[content_type.value]["error_message"].format(
                        entry=content_value
                    )
                )

        return True

    @property
    def changed(self) -> bool:
        """
        some docstring
        """
        return self._load_aliases() != self._aliases

    def add_or_update(self, alias: FirewallAlias) -> None:
        """
        some docstring.
        """

        if self.validate_content(content_type=alias.type, content_values=alias.content):

            if alias.interface:
                self.is_interface(alias.interface)

            existing_alias: Optional[FirewallAlias] = next(
                (a for a in self._aliases if a.name == alias.name), None
            )

            if existing_alias:
                alias.__dict__.pop("uuid")
                existing_alias.__dict__.update(alias.__dict__)
            else:
                self._aliases.append(alias)

    def find(self, **kwargs) -> Optional[FirewallAlias]:
        """
        some docstring
        """

        for alias in self._aliases:
            match = all(
                getattr(alias, key, None) == value for key, value in kwargs.items()
            )
            if match:
                return alias
        return None

    def delete(self, alias: FirewallAlias) -> bool:
        """
        some docstring
        """

        existing_alias: Optional[FirewallAlias] = next(
            (a for a in self._aliases if a.name == alias.name), None
        )

        if existing_alias:
            self._aliases.remove(existing_alias)
            return True
        return False

    def save(self) -> bool:
        """
        some doctsring
        """

        if not self.changed:
            return False

        filter_element: Element = self._config_xml_tree.find(
            self._config_maps[self._module_name]["alias"]
        )

        # Remove specific child elements (e.g., 'alias') from filter_element
        for alias_element in list(
            filter_element.findall("alias")
        ):  # Use list() to avoid modification during iteration
            filter_element.remove(alias_element)

        # Now, add the updated elements back directly to filter_element
        filter_element.extend([alias.to_etree() for alias in self._aliases])

        # Write the updated XML tree to the file
        tree: ElementTree = ElementTree(self._config_xml_tree)

        # raise ValueError([(test.tag, test.text) for test in list(filter_element)[0]])

        tree.write(self._config_path, encoding="utf-8", xml_declaration=True)

        # Reload the configuration to reflect the updated changes

        self._config_xml_tree = self._load_config()

        return True