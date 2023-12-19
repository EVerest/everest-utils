from pathlib import Path

import pytest

from ._magic_probe_module.parser.everest_interface_parser import EverestInterfaceParser as _EverestInterfaceParser
from ._magic_probe_module.parser.everest_type_parser import EverestTypeParser as _EverestTypeParser
from ._magic_probe_module.types.everest_config_schema import EverestConfigSchema as _EverestConfigSchema
from ._configuration.everest_environment_setup import EverestEnvironmentCoreConfiguration, \
    EverestEnvironmentProbeModuleConfiguration
from ._magic_probe_module.magic_probe_module import MagicProbeModule
from ._magic_probe_module.magic_probe_module_configurator import MagicProbeModuleConfigurator
from ._magic_probe_module.types.everest_module_manifest_schema import \
    EverestModuleManifestSchema as _EverestModuleManifestSchema
from ._magic_probe_module.value_generator import ValueGenerator
import yaml

from .everest_core import EverestCore


@pytest.fixture()
def magic_probe_module_configurator(core_config: EverestEnvironmentCoreConfiguration) -> MagicProbeModuleConfigurator:
    everest_config = _EverestConfigSchema(**yaml.safe_load(core_config.template_everest_config_path.read_text()))

    interfaces_directory = core_config.everest_core_path / "share" / "everest" / "interfaces"
    modules_dir = core_config.everest_core_path / "libexec" / "everest" / "modules"

    everest_interfaces = _EverestInterfaceParser().parse([interfaces_directory])

    everest_manifests = {}
    for f in modules_dir.glob("*"):
        if (f / "manifest.yaml").exists():
            everest_manifests[f.name] = _EverestModuleManifestSchema(
                **yaml.safe_load((f / "manifest.yaml").read_text()))

    configurator = MagicProbeModuleConfigurator(
        everest_config=everest_config,
        interfaces=everest_interfaces,
        manifests=everest_manifests
    )

    return configurator


@pytest.fixture
def magic_probe_module(core_config: EverestEnvironmentCoreConfiguration, magic_probe_module_configurator: MagicProbeModuleConfigurator, everest_core: EverestCore) -> MagicProbeModule:

    types_directory = core_config.everest_core_path / "share" / "everest" / "types"
    everest_types = _EverestTypeParser().parse([types_directory])

    return MagicProbeModule(
        interface_implementations=magic_probe_module_configurator.get_interface_implementations(),
        connections=magic_probe_module_configurator.get_requirements(),
        module_id=magic_probe_module_configurator.probe_module_id,
        session=everest_core.get_runtime_session(),
        types=list(everest_types.values())
    )


@pytest.fixture
def probe_module_config(request, magic_probe_module_configurator) -> EverestEnvironmentProbeModuleConfiguration | None:
    return EverestEnvironmentProbeModuleConfiguration(
        module_id=magic_probe_module_configurator.probe_module_id,
        connections={k: [t[0] for t in requirements] for k, requirements in
                     magic_probe_module_configurator.get_requirements().items()}
    )
