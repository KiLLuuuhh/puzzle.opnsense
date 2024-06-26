# Copyright: (c) 2023, Puzzle ITC
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the ansible_collections.puzzle.opnsense.plugins.modules.test_system_high_availability_settings"""  # pylint: disable=line-too-long

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock
import os

from ansible_collections.puzzle.opnsense.plugins.modules.system_high_availability_settings import (
    check_hasync_node,
    synchronize_states,
    disable_preempt,
    disconnect_dialup_interfaces,
    synchronize_interface,
    synchronize_peer_ip,
    remote_system_synchronization,
    services_to_synchronize,
    validate_ipv4,
)

from ansible_collections.puzzle.opnsense.plugins.module_utils.module_index import (
    VERSION_MAP,
)

from ansible_collections.puzzle.opnsense.plugins.module_utils.config_utils import (
    OPNsenseModuleConfig,
)

from ansible_collections.puzzle.opnsense.plugins.module_utils.interfaces_assignments_utils import (
    OPNSenseGetInterfacesError,
)

import pytest


TEST_VERSION_MAP = {
    "OPNsense Test": {
        "system_high_availability_settings": {
            # Add other mappings here
            "hasync": "hasync",
            "synchronize_states": "hasync/pfsyncenabled",
            "disable_preempt": "hasync/disablepreempt",
            "disconnect_dialup_interfaces": "hasync/disconnectppps",
            "synchronize_interface": "hasync/pfsyncinterface",
            "synchronize_peer_ip": "hasync/pfsyncpeerip",
            "synchronize_config_to_ip": "hasync/synchronizetoip",
            "remote_system_username": "hasync/username",
            "remote_system_password": "hasync/password",
            "php_requirements": [
                "/usr/local/etc/inc/interfaces.inc",
                "/usr/local/etc/inc/util.inc",
                "/usr/local/etc/inc/config.inc",
                "/usr/local/etc/inc/plugins.inc",
            ],
        },
    }
}


XML_CONFIG_EMPTY: str = """<?xml version="1.0"?>
    <opnsense>
    </opnsense>
    """

XML_CONFIG: str = """<?xml version="1.0"?>
    <opnsense>
      <hasync>
        <pfsyncinterface>lan</pfsyncinterface>
        <synchronizetoip/>
        <username/>
        <password/>
      </hasync>
    </opnsense>
    """


@pytest.fixture(scope="function")
def sample_config(request):
    """
    Fixture that creates a temporary file with a test XML configuration.
    The file  is used in the tests.

    Returns:
    - str: The path to the temporary file.
    """
    with patch(
        "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",  # pylint: disable=line-too-long
        return_value="OPNsense Test",
    ), patch.dict(VERSION_MAP, TEST_VERSION_MAP, clear=True):
        # Create a temporary file with a name based on the test function
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(request.param.encode())
            temp_file.flush()
        with OPNsenseModuleConfig(
            module_name="system_high_availability_settings",
            config_context_names=["system_high_availability_settings"],
            path=temp_file.name,
            check_mode=True,
        ) as config:
            yield config

    # Cleanup after the fixture is used
    os.unlink(temp_file.name)


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.modules.system_high_availability_settings.opnsense_utils.run_command",  # pylint: disable=line-too-long
    return_value={"stdout": "opt2:vagrant,lan:LAN", "stderr": None},
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG_EMPTY], indirect=True)
def test_check_hasync_node(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    assert sample_config.get("hasync") is None
    check_hasync_node(sample_config)
    assert sample_config.get("hasync") is not None
    assert sample_config.get("synchronize_interface").text == "lan"

    assert sample_config.get("synchronize_config_to_ip") is not None
    assert sample_config.get("synchronize_config_to_ip").text is None

    assert sample_config.get("remote_system_username") is not None
    assert sample_config.get("remote_system_username").text is None

    assert sample_config.get("remote_system_password") is not None
    assert sample_config.get("remote_system_password").text is None


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_synchronize_states(mocked_version_utils: MagicMock, sample_config):
    synchronize_states(sample_config, True)
    assert sample_config.get("synchronize_states").text == "on"
    synchronize_states(sample_config, False)
    assert sample_config.get("synchronize_states") is None


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_disable_preempt(mocked_version_utils: MagicMock, sample_config):
    disable_preempt(sample_config, True)
    assert sample_config.get("disable_preempt").text == "on"
    disable_preempt(sample_config, False)
    assert sample_config.get("disable_preempt") is None


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_disconnect_dialup_interfaces(mocked_version_utils: MagicMock, sample_config):
    disconnect_dialup_interfaces(sample_config, True)
    assert sample_config.get("disconnect_dialup_interfaces").text == "on"
    disconnect_dialup_interfaces(sample_config, False)
    assert sample_config.get("disconnect_dialup_interfaces") is None


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.opnsense_utils.run_command",
    return_value={"stdout": "opt2:vagrant,lan:LAN", "stderr": None},
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_synchronize_interface(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    synchronize_interface(sample_config, "vagrant")
    assert sample_config.get("synchronize_interface").text == "opt2"
    synchronize_interface(sample_config, "LAN")
    assert sample_config.get("synchronize_interface").text == "lan"
    with pytest.raises(ValueError) as excinfo:
        synchronize_interface(sample_config, "wan")
    assert (
        str(excinfo.value)
        == "'wan' is not a valid interface. If the interface exists, ensure it is enabled and also not virtual."
    )


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.opnsense_utils.run_command",
    return_value={"stdout": "", "stderr": None},
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_synchronize_interface_failure(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    with pytest.raises(OPNSenseGetInterfacesError) as excinfo:
        synchronize_interface(sample_config, "LAN")
    assert "error encountered while getting interfaces, no interfaces available" in str(
        excinfo.value
    )


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.opnsense_utils.run_command",
    return_value={"stdout": "", "stderr": "there was an error"},
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_synchronize_interface_success(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    with pytest.raises(OPNSenseGetInterfacesError) as excinfo:
        synchronize_interface(sample_config, "LAN")
    assert "error encountered while getting interfaces" in str(excinfo.value)


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_synchronize_peer_ip(mocked_version_utils: MagicMock, sample_config):
    synchronize_peer_ip(sample_config, "240.0.0.240")
    assert sample_config.get("synchronize_peer_ip").text == "240.0.0.240"
    synchronize_peer_ip(sample_config, None)
    assert sample_config.get("synchronize_peer_ip") is None
    with pytest.raises(ValueError) as excinfo:
        synchronize_peer_ip(sample_config, "test")
    assert (
        str(excinfo.value)
        == "Setting synchronize_peer_ip has to be a valid IPv4 address"
    )


def test_validate_ipv4():
    assert validate_ipv4("240.0.0.240")
    assert not validate_ipv4("test")
    assert not validate_ipv4("510.2440.-1.3")
    assert not validate_ipv4("240.0.0.240.1")
    assert not validate_ipv4("240.0.0.")
    assert not validate_ipv4("240.0.0")
    assert not validate_ipv4("2a02:150:a60d::2df:94:1:510")


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_remote_system_synchronization(mocked_version_utils: MagicMock, sample_config):
    remote_system_synchronization(sample_config, "127.0.0.1", "test", "vagrant")
    assert sample_config.get("synchronize_config_to_ip").text == "127.0.0.1"
    assert sample_config.get("remote_system_username").text == "test"
    assert sample_config.get("remote_system_password").text == "vagrant"

    remote_system_synchronization(sample_config, None, None, None)
    assert sample_config.get("synchronize_config_to_ip").text == "127.0.0.1"
    assert sample_config.get("remote_system_username").text == "test"
    assert sample_config.get("remote_system_password").text == "vagrant"

    remote_system_synchronization(sample_config, None, "test", "vagrant")
    assert sample_config.get("synchronize_config_to_ip") is not None
    assert sample_config.get("synchronize_config_to_ip").text is None
    assert sample_config.get("remote_system_username").text == "test"
    assert sample_config.get("remote_system_password").text == "vagrant"


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.opnsense_utils.run_command",
    return_value={
        "stdout_lines": [
            "aliases,Aliases",
            "authservers,Auth Servers",
            "captiveportal,Captive Portal",
            "certs,Certificates",
        ],
        "stderr": "",
    },
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_services_to_synchronize(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    for i in range(2):
        services = ["Aliases", "Auth Servers", "Captive Portal", "Certificates"]
        services_to_synchronize(sample_config, services)
        assert sample_config.get("hasync").find("synchronizealiases").text == "on"
        assert sample_config.get("hasync").find("synchronizecron") is None

    services_to_synchronize(sample_config, "Certificates")
    assert sample_config.get("hasync").find("synchronizecron") is None
    assert sample_config.get("hasync").find("synchronizealiases") is None
    assert sample_config.get("hasync").find("synchronizecerts").text == "on"
    with pytest.raises(ValueError) as excinfo:
        services_to_synchronize(sample_config, "bababooey")
    assert (
        str(excinfo.value)
        == "Service bababooey could not be found in your Opnsense installation."
        + " These are all the available services: Aliases, Auth Servers, Captive Portal, Certificates."
    )


@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.version_utils.get_opnsense_version",
    return_value="OPNsense Test",
)
@patch(
    "ansible_collections.puzzle.opnsense.plugins.module_utils.opnsense_utils.run_command",
    return_value={
        "stdout_lines": [],
        "stderr": "there was an error",
    },
)
@patch.dict(in_dict=VERSION_MAP, values=TEST_VERSION_MAP, clear=True)
@pytest.mark.parametrize("sample_config", [XML_CONFIG], indirect=True)
def test_services_to_synchronize_failure(
    mocked_version_utils: MagicMock, mocked_command_out: MagicMock, sample_config
):
    with pytest.raises(OPNSenseGetInterfacesError) as excinfo:
        services_to_synchronize(sample_config, "cron")
    assert str(excinfo.value) == "error encountered while getting services"
