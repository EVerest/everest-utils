import logging
from dataclasses import dataclass

from everest.testing.core_utils import EverestConfigAdjustmentStrategy
from everest.testing.core_utils.common import Requirement
from .magic_probe_module_config_strategy import MagicProbeModuleConfigurationStrategy
from .types.everest_config_schema import EverestConfigSchema
from .types.everest_interface import EverestInterface
from .types.everest_module_manifest_schema import EverestModuleManifestSchema


@dataclass
class _UnfulfilledRequirement:
    module_id: str
    requirement_name: str
    count: int


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

        # Determine, which fulfillments of the probe module are already defined in the config
        self._existing_fulfillments: dict[str, str] = self._collect_existing_probe_module_fulfillments()

        # Add unfullfilled requirements from all modules
        self._unfulfilled_requirements: dict[
            str, list[_UnfulfilledRequirement]] = self._determine_unfulfilled_requirements()

        # Conclude the resulting implementations
        self._probe_module_implementations: dict[str, str] = self._determine_probe_module_implementations()
        self._module_connections: dict[str, dict[str, list[str]]] = self._determine_module_probe_module_connections()
        self._probe_module_requirements: dict[
            str, dict[str, list[tuple[Requirement, EverestInterface]]]] = self._determine_probe_module_requirements()

    @property
    def probe_module_id(self):
        return self._probe_module_id

    def get_interface_implementations(self) -> dict[str, EverestInterface]:
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
            # probe_module_connections={k: [t[0] for t in requirements] for k, requirements in
            #                           self._probe_module_requirements.items()},
            module_id=self._probe_module_id
        )

    @staticmethod
    def _generate_implementation_id(interface_name: str, index: int):
        if index == 0:
            return interface_name
        else:
            return f"{interface_name}_{index}"

    def _determine_unfulfilled_requirements(self) -> dict[str, list[_UnfulfilledRequirement]]:
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
                        _UnfulfilledRequirement(module_id=module_id, requirement_name=requirement_name,
                                                count=remaining_requirement_count))

        return unfulfilled_requirements

    def _collect_existing_probe_module_fulfillments(self) -> dict[str, str]:
        """ Searches all already existing fulfillments in the provided configuration.
        Returns map of implementation_id to interface name.
        """

        existing_fulfillments = {}

        for module_id, mod in self._everest_config.active_modules.items():
            manifest = self._manifests[mod.module]
            for requirement_name, requirement in manifest.requires.items():
                existing_fulfillments.update(
                    {c.implementation_id: requirement.interface for c in mod.connections.get(requirement_name, [])
                     if c.module_id == self._probe_module_id})

        return existing_fulfillments

    def _determine_probe_module_implementations(self) -> dict[str, str]:
        interfaces = self._existing_fulfillments.copy()

        existing_implementations_by_interface = {}  # mapping interface name to list of implementation_ids
        for implementation_id, interface in self._existing_fulfillments.items():
            existing_implementations_by_interface.setdefault(interface, []).append(implementation_id)

        for interface, requirement_list in self._unfulfilled_requirements.items():
            requirement_count = max(req.count for req in requirement_list)

            # in addition to existing implementation ids, we generate new ones
            existing_implementation_ids = existing_implementations_by_interface.get(interface, [])
            added_implementation_ids = [
                self._generate_implementation_id(interface, len(existing_implementation_ids) + i)
                for i in range(requirement_count - len(existing_implementation_ids))]

            # avoid weird special case: the newly generated names equal the config-defined ones
            assert len(set(existing_implementation_ids + added_implementation_ids)) >= requirement_count, (
                f"existing implementation ids for interface {interface} interfere with magic probe module; please consider renaming implementation ids {existing_implementations_by_interface.get(interface, [])} in config")

            for implementation_id in added_implementation_ids:
                interfaces[implementation_id] = interface
        logging.warning(f"MP interfaces: {interfaces}")

        return interfaces

    def _determine_module_probe_module_connections(self) -> dict[str, dict[str, list[str]]]:
        """ Determine for each module the probe module's implementations it will require."""
        module_connections = {}

        implementations_by_interface = {}  # mapping interface name to list of implementation_ids
        for implementation_id, interface in self._probe_module_implementations.items():
            implementations_by_interface.setdefault(interface, []).append(implementation_id)

        for interface, requirement_list in self._unfulfilled_requirements.items():
            for req in requirement_list:
                current_module_connections = module_connections.setdefault(req.module_id, {})
                current_module_connections[req.requirement_name] = [implementations_by_interface[interface][i] for i in
                                                                    range(req.count)]
        return module_connections

    def _determine_probe_module_requirements(self) -> dict[str, dict[str, list[tuple[Requirement, EverestInterface]]]]:
        """ Determine the requirements of the probe module itself by collecting all provided interface implementations """
        probe_module_requirements = {}

        for module_id, mod in self._everest_config.active_modules.items():
            manifest = self._manifests[mod.module]
            if manifest.provides:
                for implementation_id, provides in manifest.provides.items():
                    probe_module_requirements.setdefault(provides.interface, []).append(
                        (Requirement(module_id=module_id, implementation_id=implementation_id),
                         self._interfaces_by_name[provides.interface])
                    )
        return probe_module_requirements


