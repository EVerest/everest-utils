from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Union, Callable


class OCPPConfigAdjustmentStrategy(ABC):
    """ Strategy that manipulates a OCPP config when called. Cf. EverestConfigurationAdjustmentStrategy class
    """

    @abstractmethod
    def adjust_ocpp_configuration(self, config: dict) -> dict:
        """ Adjusts the provided configuration by making a (deep) copy and returning the adjusted configuration. """


class OCPPConfigAdjustmentStrategyWrapper(OCPPConfigAdjustmentStrategy):
    """ Simple OCPPConfigAdjustmentStrategy from a callback function.
    """

    def __init__(self, callback: Callable[[dict], dict]):
        self._callback = callback

    def adjust_ocpp_configuration(self, config: dict) -> dict:
        """ Adjusts the provided configuration by making a (deep) copy and returning the adjusted configuration. """
        config = deepcopy(config)
        return self._callback(config)


class LibOCPPConfigurationHelperBase(ABC):
    """ Helper for parsing / adapting the LibOCPP configuration and dumping it a database file. """

    def generate_ocpp_config(self,
                             target_ocpp_config_file: Path,
                             target_ocpp_user_config_file: Path,
                             source_ocpp_config_file: Path,
                             central_system_host: str,
                             central_system_port: Union[str, int],
                             configuration_strategies: list[OCPPConfigAdjustmentStrategy] | None = None):
        config = json.loads(source_ocpp_config_file.read_text())

        configuration_strategies = configuration_strategies if configuration_strategies else []

        for v in [self._get_default_strategy(central_system_port, central_system_host)] + configuration_strategies:
            config = v.adjust_ocpp_configuration(config)

        with target_ocpp_config_file.open("w") as f:
            json.dump(config, f)
        target_ocpp_user_config_file.write_text("{}")

    @abstractmethod
    def _get_default_strategy(self, central_system_port: int | str,
                              central_system_host: str) -> OCPPConfigAdjustmentStrategy:
        pass


class LibOCPP16ConfigurationHelper(LibOCPPConfigurationHelperBase):
    def _get_default_strategy(self, central_system_port, central_system_host):
        def adjust_ocpp_configuration(config: dict) -> dict:
            config = deepcopy(config)
            charge_point_id = config["Internal"]["ChargePointId"]
            config["Internal"][
                "CentralSystemURI"] = f"{central_system_host}:{central_system_port}/{charge_point_id}"
            return config

        return OCPPConfigAdjustmentStrategyWrapper(adjust_ocpp_configuration)


class _OCPP201NetworkConnectionProfileAdjustment(OCPPConfigAdjustmentStrategy):
    """ Adjusts the OCPP 2.0.1 Network Connection Profile by injecting the right host, port and chargepoint id.

    This is utilized by the `LibOCPP201ConfigurationHelper`.

    """

    def __init__(self, central_system_port: int | str, central_system_host: str):
        self._central_system_port = central_system_port
        self._central_system_host = central_system_host

    def adjust_ocpp_configuration(self, config: dict):
        config = deepcopy(config)
        network_connection_profiles = json.loads(self._get_value_from_v201_config(
            config, "InternalCtrlr", "NetworkConnectionProfiles", "Actual"))
        for network_connection_profile in network_connection_profiles:
            security_profile = network_connection_profile["connectionData"]["securityProfile"]
            protocol = "ws" if security_profile == 1 else "wss"
            network_connection_profile["connectionData"][
                "ocppCsmsUrl"] = f"{protocol}://{self._central_system_host}:{self._central_system_port}"
        self._set_value_in_v201_config(config, "InternalCtrlr", "NetworkConnectionProfiles",
                                       "Actual", json.dumps(network_connection_profiles))
        return config

    @staticmethod
    def _get_value_from_v201_config(ocpp_config: json, component_name: str, variable_name: str,
                                    variable_attribute_type: str):
        for component in ocpp_config:
            if (component["name"] == component_name):
                return component["variables"][variable_name]["attributes"][variable_attribute_type]

    @staticmethod
    def _set_value_in_v201_config(ocpp_config: json, component_name: str, variable_name: str,
                                  variable_attribute_type: str,
                                  value: str):
        for component in ocpp_config:
            if (component["name"] == component_name):
                component["variables"][variable_name]["attributes"][variable_attribute_type] = value
                return


class LibOCPP201ConfigurationHelper(LibOCPPConfigurationHelperBase):

    def _get_default_strategy(self, central_system_port: int | str,
                              central_system_host: str) -> OCPPConfigAdjustmentStrategy:
        return _OCPP201NetworkConnectionProfileAdjustment(central_system_port, central_system_host)

