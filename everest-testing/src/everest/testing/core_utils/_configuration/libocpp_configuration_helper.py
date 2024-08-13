from __future__ import annotations

import os
from glob import glob
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
                             target_ocpp_config_path: Path,
                             target_ocpp_user_config_file: Path,
                             source_ocpp_config_path: Path,
                             central_system_host: str,
                             central_system_port: Union[str, int],
                             configuration_strategies: list[OCPPConfigAdjustmentStrategy] | None = None):
        config = self._get_config(source_ocpp_config_path)

        configuration_strategies = configuration_strategies if configuration_strategies else []

        for v in [self._get_default_strategy(central_system_port, central_system_host)] + configuration_strategies:
            config = v.adjust_ocpp_configuration(config)

        self._store_config(config, target_ocpp_config_path)
        target_ocpp_user_config_file.write_text("{}")

    @abstractmethod
    def _get_config(self, source_ocpp_config_path: Path):
        pass

    @abstractmethod
    def _get_default_strategy(self, central_system_port: int | str,
                              central_system_host: str) -> OCPPConfigAdjustmentStrategy:
        pass

    @abstractmethod
    def _store_config(self, config, target_ocpp_config_file):
        pass


class LibOCPP16ConfigurationHelper(LibOCPPConfigurationHelperBase):
    def _get_config(self, source_ocpp_config_path: Path):
        return json.loads(source_ocpp_config_path.read_text())

    def _get_default_strategy(self, central_system_port, central_system_host):
        def adjust_ocpp_configuration(config: dict) -> dict:
            config = deepcopy(config)
            charge_point_id = config["Internal"]["ChargePointId"]
            config["Internal"][
                "CentralSystemURI"] = f"{central_system_host}:{central_system_port}/{charge_point_id}"
            return config

        return OCPPConfigAdjustmentStrategyWrapper(adjust_ocpp_configuration)

    def _store_config(self, config, target_ocpp_config_file):
        with target_ocpp_config_file.open("w") as f:
            json.dump(config, f)


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
        for (component, schema) in ocpp_config.items():
            if component == component_name:
                attributes = schema["properties"][variable_name]["attributes"]
                for attribute in attributes:
                    if attribute["type"] == variable_attribute_type:
                        return attribute["value"]

    @staticmethod
    def _set_value_in_v201_config(ocpp_config: json, component_name: str, variable_name: str,
                                  variable_attribute_type: str,
                                  value: str):
        for (component, schema) in ocpp_config.items():
            if component == component_name:
                attributes = schema["properties"][variable_name]["attributes"]
                for attribute in attributes:
                    if attribute["type"] == variable_attribute_type:
                        attribute["value"] = value


class LibOCPP201ConfigurationHelper(LibOCPPConfigurationHelperBase):

    def _get_config(self, source_ocpp_config_path: Path):
        config = {}
        file_list_standardized = glob(str(source_ocpp_config_path / "standardized" / "*.json"), recursive=False)
        file_list_custom = glob(str(source_ocpp_config_path / "custom" / "*.json"), recursive=False)
        file_list = file_list_standardized + file_list_custom
        for file in file_list:
            # Get component from file name
            head, tail = os.path.split(file)
            component_name, extension = os.path.splitext(tail)
            # Store json in dict
            with open(file) as f:
                config[component_name] = json.load(f)
        return config

    def _get_default_strategy(self, central_system_port: int | str,
                              central_system_host: str) -> OCPPConfigAdjustmentStrategy:
        return _OCPP201NetworkConnectionProfileAdjustment(central_system_port, central_system_host)

    def _store_config(self, config, target_ocpp_config_path):
        # Just store all in the 'standardized' folder
        path = target_ocpp_config_path / "standardized"
        for key, value in config.items():
            file_name = path / (key + '.json')
            file_name.parent.mkdir(parents=True, exist_ok=True)
            with file_name.open("w+") as f:
                json.dump(value, f)
