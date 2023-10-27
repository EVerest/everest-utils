from copy import deepcopy
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

from everest.testing.core_utils.configuration.everest_configuration_visitors.everest_configuration_visitor import \
    EverestConfigAdjustmentVisitor


@dataclass
class EvseSecurityModuleConfiguration:
    csms_ca_bundle: Optional[str] = None
    mf_ca_bundle: Optional[str] = None
    mo_ca_bundle: Optional[str] = None
    v2g_ca_bundle: Optional[str] = None
    csms_leaf_cert_directory: Optional[str] = None
    csms_leaf_key_directory: Optional[str] = None
    secc_leaf_cert_directory: Optional[str] = None
    secc_leaf_key_directory: Optional[str] = None
    private_key_password: Optional[str] = None

    @staticmethod
    def default_from_cert_path(certs_directory: Path):
        """ Return a default definition of bundles and directory given base directory. """
        return EvseSecurityModuleConfiguration(
            csms_ca_bundle=str(certs_directory / "ca/csms/CSMS_ROOT_CA.pem"),
            mf_ca_bundle=str(certs_directory / "ca/mf/MF_ROOT_CA.pem"),
            mo_ca_bundle=str(certs_directory / "ca/mo/MO_ROOT_CA.pem"),
            v2g_ca_bundle=str(certs_directory / "ca/v2g/V2G_ROOT_CA.pem"),
            csms_leaf_cert_directory=str(certs_directory / "client/csms"),
            csms_leaf_key_directory=str(certs_directory / "client/csms"),
            secc_leaf_cert_directory=str(certs_directory / "client/cso"),
            secc_leaf_key_directory=str(certs_directory / "client/cso"),
        )

    def to_module_configuration(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class EvseSecurityModuleConfigurationVisitor(EverestConfigAdjustmentVisitor):
    """ Adjusts the Everest configuration by manipulating the evse security module configuration to point
    to the correct (temporary) certificate paths.

    """

    def __init__(self,
                 configuration: EvseSecurityModuleConfiguration,
                 module_id: Optional[str] = None):
        """

        Args:
            configuration: module configuration. This will be merged into the template configuration (meaning None values are ignored/taken from the originally provided Everest configuration)
            module_id: Id of security module; if None, auto-detected by module type "EvseSecurity
        """
        self._security_module_id = module_id
        self._configuration = configuration

    def _determine_module_id(self, everest_config: Dict):
        if self._security_module_id:
            assert self._security_module_id in everest_config[
                "active_modules"], f"Module id {self._security_module_id} not found in EVerest configuration"
            return self._security_module_id
        else:
            try:
                return next(k for k, v in everest_config["active_modules"].items() if v["module"] == "EvseSecurity")
            except StopIteration:
                raise ValueError("No EvseSecurity module found in EVerest configuration")

    def adjust_everest_configuration(self, everest_config: Dict):

        adjusted_config = deepcopy(everest_config)

        module_cfg = adjusted_config["active_modules"][self._determine_module_id(adjusted_config)]

        module_cfg["config_module"] = {**module_cfg["config_module"],
                                       **self._configuration.to_module_configuration()}

        return adjusted_config
