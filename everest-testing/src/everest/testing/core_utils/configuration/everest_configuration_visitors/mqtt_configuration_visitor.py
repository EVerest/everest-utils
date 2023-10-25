import logging
from copy import deepcopy
from typing import Dict

from everest.testing.core_utils.configuration.everest_configuration_visitors.everst_configuration_visitor import EverestConfigAdjustmentVisitor


class EverestMqttConfigurationAdjustmentVisitor(EverestConfigAdjustmentVisitor):
    """ Adjusts the Everest configuration by manipulating the "settings" block to use the prober Everest UUID and
    external prefix.

    """

    def __init__(self, everest_uuid: str, mqtt_external_prefix: str):
        self._everest_uuid = everest_uuid
        self._mqtt_external_prefix = mqtt_external_prefix

    def adjust_everest_configuration(self, config: Dict) -> Dict:
        adjusted_everest_config = deepcopy(config)
        adjusted_everest_config["settings"] = {}
        adjusted_everest_config["settings"]["mqtt_everest_prefix"] = f"everest_{self._everest_uuid}"
        adjusted_everest_config["settings"]["mqtt_external_prefix"] = self._mqtt_external_prefix
        adjusted_everest_config["settings"]["telemetry_prefix"] = f"telemetry_{self._everest_uuid}"

        # make sure controller starts with a dynamic port
        adjusted_everest_config["settings"]["controller_port"] = 0

        try:
            adjusted_everest_config["active_modules"]["iso15118_car"]["config_implementation"]["main"][
                "mqtt_prefix"] = self._mqtt_external_prefix
        except KeyError:
            logging.warning("Missing key in iso15118_car config")

        return adjusted_everest_config