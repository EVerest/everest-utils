from __future__ import annotations
from copy import deepcopy
from everest.testing.core_utils.common import Requirement
from everest.testing.core_utils import EverestConfigAdjustmentStrategy


class MagicProbeModuleConfigurationStrategy(EverestConfigAdjustmentStrategy):
    """ Adjusts the Everest configuration by adding the magic probe module into an EVerest config """

    def __init__(self,
                 module_connections: dict[str, dict[str, list[str]]],
                 # probe_module_connections: dict[str, list[Requirement]],
                 module_id: str = "probe"
                 ):
        self._module_id = module_id
        # self._connections = probe_module_connections
        self._module_connections = module_connections

    def adjust_everest_configuration(self, everest_config: dict) -> dict:
        adjusted_config = deepcopy(everest_config)
        # self._add_probe_module(adjusted_config)
        self._add_required_probe_module(adjusted_config)

        return adjusted_config

    # def _add_probe_module(self, adjusted_config: dict):
    #     probe_connections = {
    #         requirement_id: [{"module_id": requirement.module_id, "implementation_id": requirement.implementation_id}
    #                          for requirement in requirements_list]
    #         for requirement_id, requirements_list in self._connections.items()}
    #
    #     active_modules = adjusted_config.setdefault("active_modules", {})
    #     active_modules[self._module_id] = {
    #         'connections': probe_connections,
    #         'module': 'ProbeModule'
    #     }

    def _add_required_probe_module(self, adjusted_config: dict):
        for module_id, module_requirements in self._module_connections.items():
            for requirement_name, fulfillments in module_requirements.items():
                assert module_id in adjusted_config["active_modules"], f"Unknown module {module_id}"
                module_config = adjusted_config["active_modules"][module_id]
                module_config.setdefault("connections", {}).setdefault(requirement_name, []).extend(
                    ({"module_id": self._module_id, "implementation_id": fulfillment} for fulfillment in fulfillments)
                )

