from typing import Dict

from everest.testing.core_utils.common import Requirement

from .magic_probe_module_config_strategy import MagicProbeModuleConfigurationStrategy
from .types.everest_config_schema import EverestConfigSchema
from .types.everest_interface import EverestInterface
from .types.everest_module_manifest_schema import EverestModuleManifestSchema
from everest.testing.core_utils import EverestConfigAdjustmentStrategy


class MagicProbeModuleConfigurator:
    """
     Visitor that auto-injects the magic probe module for every unsatisfied requirement.
    """

    def __init__(self,
                 everest_config: EverestConfigSchema,
                 interfaces: list[EverestInterface],
                 manifests: dict[str, EverestModuleManifestSchema],
                 probe_module_id: str = "probe"):
        self._manifests = manifests
        self._everest_config = everest_config
        self._interfaces_by_name = {i.interface: i for i in interfaces}
        self._probe_module_id = probe_module_id
        self._unfulfilled_requirements: dict[
            str, list[tuple[str, str, int]]] = self._determine_unfulfilled_requirements()
        self._probe_module_implementations: dict[str, str] = self._determine_probe_module_implementations()
        self._module_connections: dict[str, dict[str, list[str]]] = self._determine_module_probe_module_connections()
        self._probe_module_requirements: dict[
            str, dict[str, list[tuple[Requirement, EverestInterface]]]] = self._determine_probe_module_requirements()

    def get_interfaces(self) -> dict[str, EverestInterface]:
        """ Returns the mapping of implementation id to EverestInterface for every interface implementation
        the probe module shall provide. """
        return {k: self._interfaces_by_name[v] for k, v in self._probe_module_implementations.items()}

    def get_requirements(self):
        """ Returns the mapping of fulfillment id to a tuple of an Everest Requirement (module id + implementation id) and
         the associated interface.

         The probe module is assumed to require _any_ offered interface in the pre-existing configuration.
         """
        return self._probe_module_requirements

    def get_configuration_adjustment_strategy(self) -> EverestConfigAdjustmentStrategy:
        return MagicProbeModuleConfigurationStrategy(
            module_connections=self._module_connections,
            probe_module_connections={k: [t[0] for t in requirements] for k, requirements in
                                      self._probe_module_requirements.items()},
            module_id=self._probe_module_id
        )

    @staticmethod
    def _get_implementation_id(interface_name: str, index: int):
        if index == 0:
            return interface_name
        else:
            return f"{interface_name}_{index}"

    def _determine_unfulfilled_requirements(self) -> dict[str, list[tuple[str, str, int]]]:
        """
        :return: mapping interface -> list of requiring modules given by tuple of module id and count of required connections
        """

        unfulfilled_requirements = {}

        for module_id, mod in self._everest_config.active_modules.items():
            manifest = self._manifests[mod.module]
            for requirement_name, requirement in manifest.requires.items():
                connections = mod.connections.get(requirement_name, [])

                remaining_requirement_count = requirement.min_connections - len(connections)
                if remaining_requirement_count > 0:
                    unfulfilled_requirements.setdefault(requirement.interface, []).append(
                        (module_id, requirement_name, remaining_requirement_count))

        return unfulfilled_requirements

    def _determine_probe_module_implementations(self) -> dict[str, str]:
        interfaces = {}
        for interface, requirement_list in self._unfulfilled_requirements.items():
            requirement_count = max(requirement_count for (_, _, requirement_count) in requirement_list)
            for i in range(requirement_count):
                interfaces[self._get_implementation_id(interface, i)] = interface
        return interfaces

    def _determine_module_probe_module_connections(self) -> dict[str, dict[str, list[str]]]:
        module_connections = {}
        for interface, requirement_list in self._unfulfilled_requirements.items():

            for (module_id, requirement_name, requirement_count) in requirement_list:
                current_module_connections = module_connections.setdefault(module_id, {})
                current_module_connections[requirement_name] = [self._get_implementation_id(interface, i) for i in
                                                                range(requirement_count)]
        return module_connections

    def _determine_probe_module_requirements(self) -> dict[str, dict[str, list[tuple[Requirement, EverestInterface]]]]:
        probe_module_requirements = {}

        for module_id, mod in self._everest_config.active_modules.items():
            manifest = self._manifests[mod.module]
            if manifest.provides:
                probe_module_requirements.setdefault(module_id, []).extend((
                    (Requirement(module_id=module_id, implementation_id=implementation_id),
                     self._interfaces_by_name[provides.interface])
                    for implementation_id, provides in manifest.provides.items()
                ))
        return probe_module_requirements
