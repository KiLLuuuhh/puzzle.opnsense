# Copyright: (c) 2023, Puzzle ITC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the ansible_collections.puzzle.opnsense.plugins.module_utils.config_utils module."""

# This is probably intentional and required for the fixture
# pylint: disable=redefined-outer-name,unused-argument,protected-access

from __future__ import absolute_import, division, print_function

__metaclass__val = type

import os
from tempfile import NamedTemporaryFile
from typing import List, Dict
from unittest.mock import patch, MagicMock
from xml.etree.ElementTree import Element
from xml.etree import ElementTree

import pytest
from ansible_collections.puzzle.opnsense.plugins.module_utils.config_utils import (
    OPNsenseModuleConfig,
    UnsupportedOPNsenseVersion,
    UnsupportedModuleSettingError,
    ModuleMisconfigurationError,
    MissingConfigDefinitionForModuleError,
    UnsupportedVersionForModule,
    OPNSenseBaseEntry,
)
from xml.etree.ElementTree import ElementTree, fromstring

from ansible_collections.puzzle.opnsense.plugins.module_utils import (
    xml_utils,
)


from ansible_collections.puzzle.opnsense.plugins.module_utils.firewall_alias_utils import (
    FirewallAlias,
)

# Test version map for OPNsense versions and modules
TEST_VERSION_MAP = {
    "OPNsense Test": {
        "test_module": {
            "hostname": "system/hostname",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "test_module_2": {
            "timezone": "system/timezone",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "test_module_3": {
            "preserve_logs": "syslog/preservelogs",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "test_module_4": {
            "hasync_parent": "hasync",
            "remote_system_username": "hasync/username",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "test_module_5": {
            "alias": "Alias",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "test_module_6": {
            "rules": "filter",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "interfaces_assignments": {
            "interfaces": "interfaces",
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "missing_php_requirements": {
            "setting_1": "settings/one",
            "setting_2": "settings/two",
            # No php_requirements
            "configure_functions": {},
        },
        "missing_configure_functions": {
            "setting_1": "settings/one",
            "setting_2": "settings/two",
            # No configure_functions
            "php_requirements": [],
        },
        "invalid_php_requirements": {
            "setting_1": "settings/one",
            "setting_2": "settings/two",
            # No php_requirements and configure_functions
            "php_requirements": "must be a list instead of a string",
            "configure_functions": {
                "test_configure_function": {
                    "name": "test_configure_function",
                    "configure_params": ["param_1"],
                },
            },
        },
        "invalid_configure_functions": {
            "setting_1": "settings/one",
            "setting_2": "settings/two",
            # No php_requirements and configure_functions
            "php_requirements": ["req_1", "req_2"],
            "configure_functions": ["must", "be", "a", "dict"],
        },
    },
}

# Test XML configuration content
TEST_XML: str = """<?xml version="1.0"?>
    <opnsense>
        <system>
            <hostname>test_name</hostname>
            <timezone>test_timezone</timezone>
        </system>
        <interfaces> # GenericParentClass
            <wan> # GenericParentClass
                <if>em2</if> # GenericChildClass
                <ipaddr>dhcp</ipaddr>
                <dhcphostname/>
                <mtu/>
                <subnet/>
                <gateway/>
                <media/>
                <mediaopt/>
                <blockbogons>1</blockbogons>
                <ipaddrv6>dhcp6</ipaddrv6>
                <dhcp6-ia-pd-len>0</dhcp6-ia-pd-len>
                <blockpriv>1</blockpriv>
                <descr>WAN</descr>
                <lock>1</lock>
            </wan>
            <lan>
                <if>em1</if>
                <descr>LAN</descr>
                <enable>1</enable>
                <lock>1</lock>
                <spoofmac/>
                <blockbogons>1</blockbogons>
                <ipaddr>192.168.56.10</ipaddr>
                <subnet>21</subnet>
                <ipaddrv6>track6</ipaddrv6>
                <track6-interface>wan</track6-interface>
                <track6-prefix-id>0</track6-prefix-id>
            </lan>
            <opt1>
                <if>em3</if>
                <descr>DMZ</descr>
                <spoofmac/>
                <lock>1</lock>
            </opt1>
            <opt2>
                <if>em0</if>
                <descr>VAGRANT</descr>
                <enable>1</enable>
                <lock>1</lock>
                <spoofmac/>
                <ipaddr>dhcp</ipaddr>
                <dhcphostname/>
                <alias-address/>
                <alias-subnet>32</alias-subnet>
                <dhcprejectfrom/>
                <adv_dhcp_pt_timeout/>
                <adv_dhcp_pt_retry/>
                <adv_dhcp_pt_select_timeout/>
                <adv_dhcp_pt_reboot/>
                <adv_dhcp_pt_backoff_cutoff/>
                <adv_dhcp_pt_initial_interval/>
                <adv_dhcp_pt_values>SavedCfg</adv_dhcp_pt_values>
                <adv_dhcp_send_options/>
                <adv_dhcp_request_options/>
                <adv_dhcp_required_options/>
                <adv_dhcp_option_modifiers/>
                <adv_dhcp_config_advanced/>
                <adv_dhcp_config_file_override/>
            <adv_dhcp_config_file_override_path/>
            </opt2>
            <lo0>
                <internal_dynamic>1</internal_dynamic>
                <descr>Loopback</descr>
                <enable>1</enable>
                <if>lo0</if>
                <ipaddr>127.0.0.1</ipaddr>
                <ipaddrv6>::1</ipaddrv6>
                <subnet>8</subnet>
                <subnetv6>128</subnetv6>
                <type>none</type>
                <virtual>1</virtual>
            </lo0>
            <openvpn>
                <internal_dynamic>1</internal_dynamic>
                <enable>1</enable>
                <if>openvpn</if>
                <descr>OpenVPN</descr>
                <type>group</type>
                <virtual>1</virtual>
                <networks/>
            </openvpn>
        </interfaces>
        <syslog>
        </syslog>
        <settings>
            <one>1</one>
            <two>2</two>
        </settings>
        <filter>
            <rule uuid="9c7ecb2c-49f3-4750-bc67-d5b666541999">
                <type>pass</type>
                <interface>wan</interface>
                <ipprotocol>inet</ipprotocol>
                <statetype>keep state</statetype>
                <descr>Allow SSH access</descr>
                <protocol>tcp</protocol>
                <source>
                   <any/>
                </source>
                <destination>
                   <any/>
                   <port>22</port>
                </destination>
            </rule>
            <rule>
                <type>pass</type>
                <interface>wan</interface>
                <ipprotocol>inet</ipprotocol>
                <statetype>keep state</statetype>
                <descr>Allow SSH access</descr>
                <protocol>tcp</protocol>
                <source>
                   <any/>
                </source>
                <destination>
                   <any/>
                   <port>22</port>
                </destination>
                <extra>
                    this is an extra attribute
                </extra>
            </rule>
        </filter>
        <Alias version="1.0.0">
            <alias uuid="ad0fd5d4-6797-4521-9ee4-df3e16de31d0">
                <enabled>1</enabled>
                <name>host_test</name>
                <type>host</type>
                <proto/>
                <interface/>
                <counters>0</counters>
                <updatefreq/>
                <content>10.0.0.1</content>
                <description>host_test</description>
            </alias>
            <alias uuid="3fc15914-8492-4a67-b990-aefd08d1c6a4">
                <enabled>1</enabled>
                <name>network_test</name>
                <type>network</type>
                <proto/>
                <interface/>
                <counters>0</counters>
                <updatefreq/>
                <content>192.168.0.0</content>
                <description>network_test</description>
            </alias>
        </Alias>
        <hasync>
            <username />
        </hasync>
    </opnsense>
    """


@pytest.fixture(scope="function")
def sample_config_path(request):
    """
    Fixture that creates a temporary file with a test XML configuration.
    The file  is used in the tests.

    Returns:
    - str: The path to the temporary file.
    """
    with patch(
        "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",  # pylint: disable=line-too-long
        return_value="OPNsense Test",
    ), patch(
        "ansible_collections.puzzle.opnsense.plugins.module_utils.module_index.VERSION_MAP",
        TEST_VERSION_MAP,
    ):
        # Create a temporary file with a name based on the test function
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(TEST_XML.encode())
            temp_file.flush()
            yield temp_file.name

    # Cleanup after the fixture is used
    os.unlink(temp_file.name)


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense X.X.X",
)
def test_unsupported_opnsense_version(
    mocked_version_util: MagicMock, sample_config_path
):
    """
    Test case to verify that an UnsupportedOPNsenseVersion exception is raised
    when attempting to initialize OPNsenseModuleConfig with an unsupported OPNsense version.

    Args:
    - mocked_version_util (MagicMock): A mock for version_utils.get_opnsense_version.
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with pytest.raises(
        UnsupportedOPNsenseVersion,
        match="OPNsense version 'OPNsense X.X.X' not supported by puzzle.opnsense collection",
    ):
        _val = OPNsenseModuleConfig(
            module_name="test_module",
            config_context_names=["test_module"],
            path=sample_config_path,
            check_mode=False,
        )


def test_unsupported_module(sample_config_path):
    """
    Test case to verify that an UnsupportedVersionForModule exception is raised
    when attempting to initialize OPNsenseModuleConfig with an unsupported module.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with pytest.raises(
        UnsupportedVersionForModule,
        match=r"Config context 'unsupported_module' not supported "
        "for OPNsense version 'OPNsense Test'.",
    ):
        _val = OPNsenseModuleConfig(
            module_name="unsupported_module",
            config_context_names=["unsupported_module"],
            path=sample_config_path,
            check_mode=False,
        )


def test_unsupported_module_setting(sample_config_path):
    """
    Test case to verify that an UnsupportedModuleSettingError exception is raised
    when attempting to retrieve an unsupported module setting.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        "test_module", config_context_names=["test_module"], path=sample_config_path
    ) as new_config:
        with pytest.raises(
            UnsupportedModuleSettingError,
            match="Setting 'unsupported' is not supported in module 'test_module' "
            "for OPNsense version 'OPNsense Test'",
        ):
            _val = new_config.get("unsupported")


def test_setting_from_two_contexts_accessible(sample_config_path):
    """
    Test case to verify that a OPNsenseModuleConfig with multiple context can access
    settings of any given context.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        "test_module",
        config_context_names=["test_module", "test_module_2"],
        path=sample_config_path,
    ) as new_config:
        hostname = new_config.get("hostname")
        timezone = new_config.get("timezone")

        assert hostname.text == "test_name"
        assert timezone.text == "test_timezone"


def test_setting_from_another_context_raises_error(sample_config_path):
    """
    Test case to verify that a OPNsenseModuleConfig with multiple context cannot access
    a context it has not been initialized with.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        "test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
    ) as new_config:
        with pytest.raises(
            UnsupportedModuleSettingError,
            match="Setting 'timezone' is not supported in module 'test_module' "
            "for OPNsense version 'OPNsense Test'",
        ):
            _timezone = new_config.get("timezone")


def test_php_requirements_must_be_present(sample_config_path):
    """
    Test case to verify that a MissingConfigDefinitionForModuleError exception is raised
    when attempting to retrieve PHP requirements that are missing for a module.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="missing_php_requirements",
        config_context_names=["missing_php_requirements"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        with pytest.raises(
            MissingConfigDefinitionForModuleError,
            match=r"Module 'missing_php_requirements' has no php_requirements defined in "
            "the ansible_collections.puzzle.opnsense.plugins.module_utils.module_index.VERSION_MAP for given "  # pylint: disable=line-too-long
            "OPNsense version 'OPNsense Test'.",
        ):
            _val = new_config._get_php_requirements()


def test_config_functions_must_be_present(sample_config_path):
    """
    Test case to verify that a MissingConfigDefinitionForModuleError exception is raised
    when attempting to retrieve configure functions that are missing for a module.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="missing_configure_functions",
        config_context_names=["missing_configure_functions"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        with pytest.raises(
            MissingConfigDefinitionForModuleError,
            match=r"Module 'missing_configure_functions' has no configure_functions defined in "
            "the ansible_collections.puzzle.opnsense.plugins.module_utils.module_index.VERSION_MAP for given "  # pylint: disable=line-too-long
            "OPNsense version 'OPNsense Test'.",
        ):
            _val = new_config._get_configure_functions()


def test_php_requirements_must_be_list(sample_config_path):
    """
    Test case to verify that a ModuleMisconfigurationError exception is raised
    when PHP requirements are not provided as a list.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="invalid_php_requirements",
        config_context_names=["invalid_php_requirements"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        with pytest.raises(
            ModuleMisconfigurationError,
            match=(
                r"PHP requirements \(php_requirements\) for the module 'invalid_php_requirements' "
                r"are not provided as a list in the VERSION_MAP using OPNsense version"
                r"'OPNsense Test'."
            ),
        ):
            _val = new_config._get_php_requirements()


def test_configure_functions_must_be_dict(sample_config_path):
    """
    Test case to verify that a ModuleMisconfigurationError exception is raised
    when configure functions are not provided as a dictionary.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="invalid_configure_functions",
        config_context_names=["invalid_configure_functions"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        with pytest.raises(
            ModuleMisconfigurationError,
            match=(
                r"Configure functions \(configure_functions\) for the module "
                r"'invalid_configure_functions' are "
                r"not provided as a list in the VERSION_MAP using OPNsense version "
                r"'OPNsense Test'."
            ),
        ):
            _val = new_config._get_configure_functions()


def test_get_php_requirements(sample_config_path):
    """
    Test case to verify the correct retrieval of PHP requirements for a module.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        requirements: List[str] = new_config._get_php_requirements()

        assert (
            requirements
            == TEST_VERSION_MAP["OPNsense Test"]["test_module"]["php_requirements"]
        )


def test_get_configure_functions(sample_config_path):
    """
    Test case to verify the correct retrieval of configure functions for a module.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        requirements: Dict = new_config._get_configure_functions()

        assert (
            requirements
            == TEST_VERSION_MAP["OPNsense Test"]["test_module"]["configure_functions"]
        )


def test_changed(sample_config_path):
    """
    Test case to verify that the `changed` property correctly identifies changes
    in the OPNsense configuration.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_config.set(value="testtest", setting="hostname")
        assert new_config.changed
        new_config.save()


def test_get_setting(sample_config_path):
    """
    Test case to verify the correct retrieval of a specific setting from the OPNsense configuration.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        hostname_setting: Element = new_config.get("hostname")
        assert isinstance(hostname_setting, Element)
        assert "test_name" == hostname_setting.text
        new_config.save()


def test_save_on_changed(sample_config_path):
    """
    Test case to verify that the configuration is saved when changes are made.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_config.set(value="testtest", setting="hostname")
        assert new_config.save()


def test_save_on_not_changed(sample_config_path):
    """
    Test case to verify that the configuration is not saved when no changes are made.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        assert not new_config.save()


def test_diff_on_change(sample_config_path):
    """
    Test case to verify that the `diff` property correctly identifies changes
    in the OPNsense configuration.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_config.set(value="testtest", setting="hostname")
        diff = new_config.diff

        assert diff == {
            "before": {
                "system/hostname": "test_name",
            },
            "after": {
                "system/hostname": "testtest",
            },
        }
        new_config.save()


def test_diff_on_no_change(sample_config_path):
    """
    Test case to verify that the `diff` property correctly identifies no changes
    in the OPNsense configuration.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        diff = new_config.diff
        assert diff["before"] == diff["after"]


def test_set_with_missing_element(sample_config_path):
    """
    Test case to verify that we can set options for which there is currently element
    in the xml tree. This is the case for example with the preserve_logs setting.
    The xml does not contain the path `syslog/preservelogs` unless the option is configured.
    In this case we expect that the module will create the object.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module_3",
        config_context_names=["test_module_3"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_config.set(value="10", setting="preserve_logs")
        diff = new_config.diff

        assert diff == {
            "before": {
                "syslog/preservelogs": "",
            },
            "after": {
                "syslog/preservelogs": "10",
            },
        }
        new_config.save()


def test_fail_set_on_parent_node(sample_config_path):
    """
    Test case to verify that setting a value for a parent node will fail.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module_4",
        config_context_names=["test_module_4"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        with pytest.raises(AttributeError):
            new_config.set("test", "hasync_parent")


def test_success_set_on_empty_leaf_node(sample_config_path):
    """
    Test case to verify that setting a leaf node with a value of None will succeed.

    Args:
    - sample_config_path (str): The path to the temporary test configuration file.
    """
    with OPNsenseModuleConfig(
        module_name="test_module_4",
        config_context_names=["test_module_4"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_config.set("test", "remote_system_username")
        assert new_config.get("remote_system_username").text == "test"
        new_config.save()


def test_multiple_get_setting(sample_config_path):
    """ """
    with OPNsenseModuleConfig(
        module_name="test_module",
        config_context_names=["test_module_5"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        assert (
            new_config.get_entries_as_objects(setting_name="alias")[0].name
            == "host_test"
        )

        new_config.save()


def test_model_registry(sample_config_path):
    """ """
    with OPNsenseModuleConfig(
        module_name="test_module_5",
        config_context_names=["test_module_5", "test_module_6"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        # check if model_registry is available
        assert new_config.model_registry

        # alias len tests
        assert len(new_config.model_registry["test_module_5"]["alias"]) == 2

        # alias integrity tests
        assert new_config.model_registry["test_module_5"]["alias"][0].tag == "alias"

        # alias find tests
        test_find_alias = new_config.find(name="host_test")

        # alias object tests
        assert test_find_alias.enabled == True
        assert test_find_alias.name == "host_test"
        assert test_find_alias.type == "host"
        assert test_find_alias.proto is None
        assert test_find_alias.interface is None
        assert test_find_alias.counters == "0"
        assert test_find_alias.updatefreq is None
        assert test_find_alias.content == "10.0.0.1"
        assert test_find_alias.description == "host_test"

        # alias update tests
        update_existing_alias: OPNSenseBaseEntry = OPNSenseBaseEntry(
            name="host_test", type="host", description="new_description"
        )

        test_update_existing_alias = new_config.find(name="host_test")

        assert test_update_existing_alias.description == "host_test"

        new_config.create_or_update(
            module="test_module_5",
            opnsense_object=update_existing_alias,
            uniqueness="name",
        )

        test_update_existing_alias = new_config.find(name="host_test")

        assert test_update_existing_alias.description == "new_description"

        assert len(new_config.model_registry["test_module_5"]["alias"]) == 2

        # alias delete tests
        delete_existing_alias = new_config.find(name="host_test")

        new_config.delete(
            module="test_module_5", tag="alias", opnsense_object=delete_existing_alias
        )

        assert len(new_config.model_registry["test_module_5"]["alias"]) == 1

        # rule len tests
        assert len(new_config.model_registry["test_module_6"]["rule"]) == 2

        # rule integrity tests
        assert new_config.model_registry["test_module_6"]["rule"][0].tag == "rule"

        # rule find tests
        test_find_rule = new_config.find(interface="wan")

        # rule object tests
        assert test_find_rule.type == "pass"
        assert test_find_rule.interface == "wan"
        assert test_find_rule.ipprotocol == "inet"
        assert test_find_rule.statetype == "keep state"
        assert test_find_rule.descr == "Allow SSH access"
        assert test_find_rule.protocol == "tcp"

        # to be discussed
        assert test_find_rule.source["any"] is None
        assert test_find_rule.destination["any"] is None
        assert test_find_rule.destination["port"] == "22"

        # rule update tests
        update_existing_rule: OPNSenseBaseEntry = OPNSenseBaseEntry(
            interface="wan", type="pass", descr="New Allow SSH access Description"
        )

        test_update_existing_rule = new_config.find(interface="wan")

        assert test_update_existing_rule.descr == "Allow SSH access"

        new_config.create_or_update(
            module="test_module_6",
            opnsense_object=update_existing_rule,
            uniqueness="interface",
        )

        test_update_existing_rule = new_config.find(interface="wan")

        assert update_existing_rule.descr == "New Allow SSH access Description"

        # rule delete tests
        delete_existing_rule = new_config.find(interface="wan")

        new_config.delete(
            module="test_module_6", tag="rule", opnsense_object=delete_existing_rule
        )

        assert len(new_config.model_registry["test_module_6"]["rule"]) == 1

        new_config.save()


def test_model_registry_firewall_alias_without_set(sample_config_path):
    """ """
    with OPNsenseModuleConfig(
        module_name="test_module_5",
        config_context_names=["test_module_5", "test_module_6"],
        path=sample_config_path,
        check_mode=False,
    ) as config:
        assert config.model_registry

        # alias len tests
        assert len(config.model_registry["test_module_5"]["alias"]) == 2

        # alias find tests
        test_new_firewall_alias: OPNSenseBaseEntry = OPNSenseBaseEntry(
            name="host_test_1",
            type="host",
            description="some random description",
            tag="alias",
        )

        test_new_firewall_alias.tag = "alias"

        config.create_or_update(
            module="test_module_5",
            opnsense_object=test_new_firewall_alias,
            uniqueness="name",
        )

        assert len(config.model_registry["test_module_5"]["alias"]) == 3

        assert config.changed

        config.save()

    with OPNsenseModuleConfig(
        module_name="test_module_5",
        config_context_names=["test_module_5", "test_module_6"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        assert len(new_config.model_registry["test_module_5"]["alias"]) == 3


def test_firewall_alias_from_ansible_module_params(sample_config_path):
    """ """

    test_params: dict = {
        "name": "test_alias",
        "type": "host",
        "description": "Test Alias",
        "enabled": True,
        "content": ["8.8.8.8-9.9.9.9", "TestHost", "192.168.0.0"],
    }

    with OPNsenseModuleConfig(
        module_name="test_module_5",
        config_context_names=["test_module_5", "test_module_6"],
        path=sample_config_path,
        check_mode=False,
    ) as config:
        new_alias: OPNSenseBaseEntry = OPNSenseBaseEntry.from_ansible_module_params(
            test_params
        )
        new_alias.tag = "alias"

        config.create_or_update(
            module="test_module_5",
            opnsense_object=new_alias,
            uniqueness="name",
        )

        assert config.changed

        config.save()

    with OPNsenseModuleConfig(
        module_name="test_module_5",
        config_context_names=["test_module_5", "test_module_6"],
        path=sample_config_path,
        check_mode=False,
    ) as new_config:
        new_alias: OPNSenseBaseEntry = new_config.find(name="test_alias")

        assert new_alias.enabled == True
        assert new_alias.name == "test_alias"
        assert new_alias.type == "host"
        assert new_alias.content == ["8.8.8.8-9.9.9.9", "TestHost", "192.168.0.0"]
        assert new_alias.description == "Test Alias"

        new_config.save()


TEST_XML: str = """<?xml version="1.0"?>
    <opnsense>
        <system>
            <hostname>test_name</hostname>
            <timezone>test_timezone</timezone>
        </system>
        <interfaces>
            <wan>
                <if>em2</if>
                <ipaddr>dhcp</ipaddr>
                <dhcphostname/>
                <mtu/>
                <subnet/>
                <gateway/>
                <media/>
                <mediaopt/>
                <blockbogons>1</blockbogons>
                <ipaddrv6>dhcp6</ipaddrv6>
                <dhcp6-ia-pd-len>0</dhcp6-ia-pd-len>
                <blockpriv>1</blockpriv>
                <descr>WAN</descr>
                <lock>1</lock>
            </wan>
            <lan>
                <if>em1</if>
                <descr>LAN</descr>
                <enable>1</enable>
                <lock>1</lock>
                <spoofmac/>
                <blockbogons>1</blockbogons>
                <ipaddr>192.168.56.10</ipaddr>
                <subnet>21</subnet>
                <ipaddrv6>track6</ipaddrv6>
                <track6-interface>wan</track6-interface>
                <track6-prefix-id>0</track6-prefix-id>
            </lan>
            <opt1>
                <if>em3</if>
                <descr>DMZ</descr>
                <spoofmac/>
                <lock>1</lock>
            </opt1>
            <opt2>
                <if>em0</if>
                <descr>VAGRANT</descr>
                <enable>1</enable>
                <lock>1</lock>
                <spoofmac/>
                <ipaddr>dhcp</ipaddr>
                <dhcphostname/>
                <alias-address/>
                <alias-subnet>32</alias-subnet>
                <dhcprejectfrom/>
                <adv_dhcp_pt_timeout/>
                <adv_dhcp_pt_retry/>
                <adv_dhcp_pt_select_timeout/>
                <adv_dhcp_pt_reboot/>
                <adv_dhcp_pt_backoff_cutoff/>
                <adv_dhcp_pt_initial_interval/>
                <adv_dhcp_pt_values>SavedCfg</adv_dhcp_pt_values>
                <adv_dhcp_send_options/>
                <adv_dhcp_request_options/>
                <adv_dhcp_required_options/>
                <adv_dhcp_option_modifiers/>
                <adv_dhcp_config_advanced/>
                <adv_dhcp_config_file_override/>
            <adv_dhcp_config_file_override_path/>
            </opt2>
            <lo0>
                <internal_dynamic>1</internal_dynamic>
                <descr>Loopback</descr>
                <enable>1</enable>
                <if>lo0</if>
                <ipaddr>127.0.0.1</ipaddr>
                <ipaddrv6>::1</ipaddrv6>
                <subnet>8</subnet>
                <subnetv6>128</subnetv6>
                <type>none</type>
                <virtual>1</virtual>
            </lo0>
            <openvpn>
                <internal_dynamic>1</internal_dynamic>
                <enable>1</enable>
                <if>openvpn</if>
                <descr>OpenVPN</descr>
                <type>group</type>
                <virtual>1</virtual>
                <networks/>
            </openvpn>
        </interfaces>
        <syslog>
        </syslog>
        <settings>
            <one>1</one>
            <two>2</two>
        </settings>
        <filter>
            <rule uuid="9c7ecb2c-49f3-4750-bc67-d5b666541999">
                <type>pass</type>
                <interface>wan</interface>
                <ipprotocol>inet</ipprotocol>
                <statetype>keep state</statetype>
                <descr>Allow SSH access</descr>
                <protocol>tcp</protocol>
                <source>
                   <any/>
                </source>
                <destination>
                   <any/>
                   <port>22</port>
                </destination>
            </rule>
            <rule>
                <type>pass</type>
                <interface>wan</interface>
                <ipprotocol>inet</ipprotocol>
                <statetype>keep state</statetype>
                <descr>Allow SSH access</descr>
                <protocol>tcp</protocol>
                <source>
                   <any/>
                </source>
                <destination>
                   <any/>
                   <port>22</port>
                </destination>
                <extra>
                    this is an extra attribute
                </extra>
            </rule>
        </filter>
        <Alias version="1.0.0">
            <alias uuid="ad0fd5d4-6797-4521-9ee4-df3e16de31d0">
                <enabled>1</enabled>
                <name>host_test</name>
                <type>host</type>
                <proto/>
                <interface/>
                <counters>0</counters>
                <updatefreq/>
                <content>10.0.0.1</content>
                <description>host_test</description>
            </alias>
            <alias uuid="3fc15914-8492-4a67-b990-aefd08d1c6a4">
                <enabled>1</enabled>
                <name>network_test</name>
                <type>network</type>
                <proto/>
                <interface/>
                <counters>0</counters>
                <updatefreq/>
                <content>192.168.0.0</content>
                <description>network_test</description>
            </alias>
        </Alias>
        <hasync>
            <username />
        </hasync>
    </opnsense>
    """


class GenericNodeClass:
    def __init__(self, tag, text=None):
        self.tag = tag
        self.text = text if text is not None else ""  # Handle None as empty string
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __getattr__(self, key):
        """
        Allows direct attribute access, e.g., parent["ipaddr"]
        """

        for child in self.children:
            if key == child.tag:
                if not len(child.children):
                    return child.text
                return child

        raise AttributeError(f"object has no Attribute with the name {key}")


class ConfigSet:
    def __init__(self, xml_string):
        self.root = self._load_config(xml_string)
        self.structure = self._parse_elements(self.root)

    def _load_config(self, xml_string: str):
        # Parse the XML string and return the root element
        return ElementTree(fromstring(xml_string)).getroot()

    def _parse_elements(self, element):
        parent_obj = GenericNodeClass(element.tag)

        # Check if the element has children
        if len(element):

            for sub_element in element:
                child_obj = self._parse_elements(sub_element)
                parent_obj.add_child(child_obj)  # Add the child to the parent
        else:
            # If no children (leaf node), just store the text content
            parent_obj = GenericNodeClass(element.tag, element.text)

        return parent_obj

def test_init(sample_config_path):

    test = ConfigSet(xml_string=TEST_XML)

    # test single objects

    assert test.structure.system.hostname == "test_name"
    assert test.structure.system.timezone == "test_timezone"

    assert test.structure.interfaces.wan.ipaddr == "dhcp"
    assert test.structure.interfaces.wan.blockbogons == "1"

    assert test.structure.interfaces.lan.ipaddr == "192.168.56.10"
    assert test.structure.interfaces.lan.blockbogons == "1"


    test.structure.interfaces.lan.descr == "dini meer"

