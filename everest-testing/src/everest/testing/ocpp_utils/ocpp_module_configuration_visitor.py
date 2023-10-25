from abc import abstractmethod, ABC
from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Union, Dict, List

from everest.testing.core_utils.common import OCPPVersion
from everest.testing.core_utils.everst_configuration_visitor import EverestConfigAdjustmentVisitor



@dataclass
class OCPPModuleConfigurationBase:
    ChargePointConfigPath: str
    MessageLogPath: str
    CertsPath: str

@dataclass
class OCPPModulePaths16(OCPPModuleConfigurationBase):
    UserConfigPath: str
    DatabasePath: str

@dataclass
class OCPPModulePaths201(OCPPModuleConfigurationBase):
    CoreDatabasePath: str
    DeviceModelDatabasePath: str


class OCPPModuleConfigurationVisitor(EverestConfigAdjustmentVisitor):
    """ Class to dynamically the configuration of an EVerest OCPP Module
    """


    def __init__(self, ocpp_paths: Union[OCPPModulePaths16, OCPPModulePaths201],
                 ocpp_module_id: str,
                 ocpp_version: OCPPVersion):
        self._ocpp_paths = ocpp_paths
        self._ocpp_module_id = ocpp_module_id
        self._ocpp_version = ocpp_version

    def adjust_everest_configuration(self, everest_config: Dict):
        """ Changes the provided configuration of the Everest "OCPP" module .

        Creates the TEST_LOGS_DIR if not existent
        """

        adjusted_config = deepcopy(everest_config)

        self._verify_module_config(adjusted_config)

        module_config = adjusted_config["active_modules"][self._ocpp_module_id]

        module_config["config_module"] = {**module_config["config_module"],
                                          **asdict(self._ocpp_paths)}

        # paths["ChargePointConfigPath"] = self.temp_ocpp_config_file.name
        # paths["MessageLogPath"] = f"{TEST_LOGS_DIR}/{self.test_function_name}-{datetime.utcnow().isoformat()}"
        # paths["CertsPath"] = self.temp_ocpp_certs_dir.name
        #
        # if self.ocpp_version == OCPPVersion.ocpp16:
        #     paths["UserConfigPath"] = self.temp_ocpp_user_config_file.name
        #     paths["DatabasePath"] = self.temp_ocpp_database_dir.name
        # elif self.ocpp_version == OCPPVersion.ocpp201:
        #     paths["CoreDatabasePath"] = self.temp_ocpp_database_dir.name
        #     paths["DeviceModelDatabasePath"] = f"{self.temp_ocpp_database_dir.name}/device_model_storage.db"

        return adjusted_config


    def _verify_module_config(self, everest_config):
        """ Get reference to OCPP module config"""
        assert "active_modules" in everest_config and self._ocpp_module_id in everest_config[
            "active_modules"], "OCPP Module is missing from EVerest config"
        ocpp_module = everest_config["active_modules"][self._ocpp_module_id]["module"]
        assert (ocpp_module == "OCPP" and self._ocpp_version == OCPPVersion.ocpp16) or (
                ocpp_module == "OCPP201" and self._ocpp_version == OCPPVersion.ocpp201), \
            f"Invalid OCCP Module {ocpp_module} for provided OCCP version {self._ocpp_version}"


