import pytest

from ._configuration.everest_environment_setup import EverestEnvironmentCoreConfiguration, \
    EverestEnvironmentProbeModuleConfiguration
from ._magic_probe_module.magic_probe_module import MagicProbeModule
from ._magic_probe_module.parser.everest_type_parser import EverestTypeParser as _EverestTypeParser
from .everest_core import EverestCore


@pytest.fixture
def magic_probe_module(core_config: EverestEnvironmentCoreConfiguration,
                       probe_module_config: EverestEnvironmentProbeModuleConfiguration | None,
                       everest_core: EverestCore) -> MagicProbeModule:

    if not probe_module_config or not probe_module_config.magic_probe_module_configurator:
        raise AssertionError("Error: Usage of magic_probe_module fixture requires the @magic_probe_module marker or an override of the probe_module_config fixture.")

    types_directory = core_config.everest_core_path / "share" / "everest" / "types"
    everest_types = _EverestTypeParser().parse([types_directory])

    magic_probe_module_configurator = probe_module_config.magic_probe_module_configurator
    return MagicProbeModule(
        interface_implementations=magic_probe_module_configurator.get_interface_implementations(),
        connections=magic_probe_module_configurator.get_requirements(),
        module_id=magic_probe_module_configurator.probe_module_id,
        session=everest_core.get_runtime_session(),
        types=list(everest_types.values()),
        strict_mode=probe_module_config.magic_probe_module_strict_mode
    )

