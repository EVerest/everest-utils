# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2023 Pionix GmbH and Contributors to EVerest
import logging
from pathlib import Path
from typing import Optional

import pytest

from everest.testing.core_utils.controller.everest_environment_setup import EverestEnvironmentProbeModuleConfiguration, \
    EverestTestEnvironmentSetup, EverestEnvironmentOCPPConfiguration, EverestEnvironmentCoreConfiguration
from everest.testing.core_utils.everest_core import EverestCore


@pytest.fixture
def probe_module_config(request) -> Optional[EverestEnvironmentProbeModuleConfiguration]:
    marker = request.node.get_closest_marker("probe_module")
    if marker:
        return EverestEnvironmentProbeModuleConfiguration(
            **marker.kwargs
        )

    return None


@pytest.fixture
def core_config(request) -> EverestEnvironmentCoreConfiguration:
    everest_prefix = Path(request.config.getoption("--everest-prefix"))

    marker = request.node.get_closest_marker("everest_core_config")
    if marker is None:
        everest_config_path = None  # config auto-detected by everest core
    else:
        path = Path('/etc/everest') if everest_prefix == '/usr' else everest_prefix / 'etc/everest'
        everest_config_path = path / marker.args[0]

    return EverestEnvironmentCoreConfiguration(
        everest_core_path=everest_prefix,
        template_everest_config_path=everest_config_path,
    )


@pytest.fixture
def ocpp_config(request) -> Optional[EverestEnvironmentOCPPConfiguration]:
    return None


@pytest.fixture
def everest_core(request,
                 tmp_path,
                 core_config: EverestEnvironmentCoreConfiguration,
                 ocpp_config: EverestEnvironmentOCPPConfiguration,
                 probe_module_config: EverestEnvironmentProbeModuleConfiguration) -> EverestCore:
    """Fixture that can be used to start and stop everest-core"""

    standalone_module_marker = request.node.get_closest_marker('standalone_module')

    environment_setup = EverestTestEnvironmentSetup(
        core_config=core_config,
        ocpp_config=ocpp_config,
        probe_config=probe_module_config,
        standalone_module=standalone_module_marker
    )

    environment_setup.setup_environment(tmp_path=tmp_path)
    yield environment_setup.everest_core

    # FIXME (aw): proper life time management, shouldn't the fixure start and stop?
    environment_setup.everest_core.stop()
