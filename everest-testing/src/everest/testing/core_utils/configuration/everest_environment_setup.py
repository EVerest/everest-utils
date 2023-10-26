# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2023 Pionix GmbH and Contributors to EVerest

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Union

import yaml

from everest.testing.core_utils.common import OCPPVersion
from everest.testing.core_utils.configuration.everest_configuration_visitors.evse_security_configuration_visitor import \
    EvseSecurityModuleConfigurationVisitor, EvseSecurityModuleConfiguration
from everest.testing.core_utils.configuration.everest_configuration_visitors.ocpp_module_configuration_visitor import \
    OCPPModuleConfigurationVisitor, \
    OCPPModulePaths16, OCPPModulePaths201
from everest.testing.core_utils.configuration.everest_configuration_visitors.persistent_store_configuration_visitor import \
    PersistentStoreConfigurationVisitor
from everest.testing.core_utils.configuration.everest_configuration_visitors.probe_module_configuration_visitor import \
    ProbeModuleConfigurationVisitor

from everest.testing.core_utils.everest_core import EverestCore, Requirement
from everest.testing.core_utils.configuration.libocpp_configuration_helper import \
    LibOCPP201ConfigurationHelper, LibOCPP16ConfigurationHelper

logging.basicConfig(level=logging.DEBUG)


@dataclass
class EverestEnvironmentOCPPConfiguration:
    libocpp_path: Path
    ocpp_version: OCPPVersion
    central_system_port: str
    ocpp_module_id: str = "ocpp"
    template_ocpp_config: Optional[
        Path] = None  # Path for OCPP config to be used; if not provided, will be determined from everest config


@dataclass
class EverestEnvironmentEvseSecurityConfiguration:
    use_temporary_certificates_folder: bool = True  # if true, configuration will be adapted to use temporary certifcates folder, this assumes a "default" file tree structure, cf. the EvseSecurityModuleConfiguration dataclass
    module_id: Optional[str] = None  # if None, auto-detected
    source_certificate_directory: Optional[Path] = None  # if provided, this will be copied to temporary path and


@dataclass
class EverestEnvironmentPersistentStoreConfiguration:
    use_temporary_folder: bool = True  # if true, a temporary persistant storage folder will be used


@dataclass
class EverestEnvironmentCoreConfiguration:
    everest_core_path: Path
    template_everest_config_path: Union[
        Path, None]  # Underlying EVerest configuration; will be copied temporarily by EverestCore and adjusted;
    # if none, config is auto-detected by everest-core


@dataclass
class EverestEnvironmentProbeModuleConfiguration:
    connections: Dict[str, List[Requirement]] = field(default_factory=dict)
    module_id: str = "probe"


class EverestTestEnvironmentSetup:
    """
     Class that prepares the environment of EVerest core and creates the EverestCore instance of a test.

     For this:
     - receives all settings / configurations required at initialization
     - calling setup_environment:
        - creates required temporary paths / file structures
        - configures EverestCore including adjustments of the EverestCore configuration (injecting temporary paths ...)
        - sets up special modules (initiates the setup of OCPPlib such as parsing the device model database)
        - creates the EverestCore instance

    """

    @dataclass
    class _EverestEnvironmentTemporaryPaths:
        """ Paths of the temporary configuration files / data """
        certs_dir: Path  # used by both OCPP and evse security
        ocpp_config_file: Path
        ocpp_user_config_file: Path
        ocpp_database_dir: Path
        ocpp_message_log_directory: Path
        persistent_store_db_path: Path

    def __init__(self,
                 core_config: EverestEnvironmentCoreConfiguration,
                 ocpp_config: Optional[EverestEnvironmentOCPPConfiguration] = None,
                 probe_config: Optional[EverestEnvironmentProbeModuleConfiguration] = None,
                 evse_security_config: Optional[EverestEnvironmentEvseSecurityConfiguration] = None,
                 persistent_store_config: Optional[EverestEnvironmentPersistentStoreConfiguration] = None,
                 standalone_module: Optional[Union[str, List[str]]] = None
                 ) -> None:
        self._core_config = core_config
        self._ocpp_config = ocpp_config
        self._probe_config = probe_config
        self._evse_security_config = evse_security_config
        self._persistent_store_config = persistent_store_config
        self._standalone_module = standalone_module
        if not self._standalone_module and self._probe_config:
            self._standalone_module = self._probe_config.module_id
        self._everest_core = None

    def setup_environment(self, tmp_path: Path):

        temporary_paths = self._create_temporary_directory_structure(tmp_path)

        configuration_visitors = self._create_everest_configuration_visitors(temporary_paths)

        self._everest_core = EverestCore(self._core_config.everest_core_path,
                                         self._core_config.template_everest_config_path,
                                         everest_configuration_adjustment_visitors=configuration_visitors,
                                         standalone_module=self._standalone_module)

        if self._ocpp_config:
            self._setup_libocpp_configuration(
                source_certs_directory=self._everest_core.etc_path / 'certs',
                temporary_paths=temporary_paths
            )

        if self._evse_security_config:
            self._setup_evse_security_configuration(temporary_paths)

    @property
    def everest_core(self) -> EverestCore:
        assert self._everest_core, "Everest Core not initialized; run 'setup_environment' first"
        return self._everest_core

    def _create_temporary_directory_structure(self, tmp_path: Path) -> _EverestEnvironmentTemporaryPaths:
        ocpp_config_dir = tmp_path / "ocpp_config"
        ocpp_config_dir.mkdir(exist_ok=True)
        certs_dir = tmp_path / "certs"
        certs_dir.mkdir(exist_ok=True)
        ocpp_logs_dir = ocpp_config_dir / "logs"
        ocpp_logs_dir.mkdir(exist_ok=True)

        persistent_store_dir = tmp_path / "persistent_storage"
        persistent_store_dir.mkdir(exist_ok=True)

        logging.info(f"temp ocpp config files directory: {ocpp_config_dir}")

        return self._EverestEnvironmentTemporaryPaths(
            ocpp_config_file=ocpp_config_dir / "config.json",
            ocpp_user_config_file=ocpp_config_dir / "user_config.json",
            ocpp_database_dir=ocpp_config_dir,
            certs_dir=certs_dir,
            ocpp_message_log_directory=ocpp_logs_dir,
            persistent_store_db_path=persistent_store_dir / "persistent_store.db"
        )

    def _create_ocpp_module_configuration_visitor(self,
                                                  temporary_paths: _EverestEnvironmentTemporaryPaths) -> OCPPModuleConfigurationVisitor:

        if self._ocpp_config.ocpp_version == OCPPVersion.ocpp16:
            ocpp_paths = OCPPModulePaths16(
                ChargePointConfigPath=str(temporary_paths.ocpp_config_file),
                MessageLogPath=str(temporary_paths.ocpp_message_log_directory),
                CertsPath=str(temporary_paths.certs_dir),
                UserConfigPath=str(temporary_paths.ocpp_user_config_file),
                DatabasePath=str(temporary_paths.ocpp_database_dir)  # self.temp_ocpp_database_dir.name
            )
        elif self._ocpp_config.ocpp_version == OCPPVersion.ocpp201:
            ocpp_paths = OCPPModulePaths201(
                ChargePointConfigPath=str(temporary_paths.ocpp_config_file),
                MessageLogPath=str(temporary_paths.ocpp_message_log_directory),
                CertsPath=str(temporary_paths.certs_dir),
                CoreDatabasePath=str(temporary_paths.ocpp_database_dir),
                DeviceModelDatabasePath=str(temporary_paths.ocpp_database_dir / "device_model_storage.db"),
            )
        else:
            raise ValueError(f"unknown  ocpp version {self._ocpp_config.ocpp_version}")

        occp_module_configuration_helper = OCPPModuleConfigurationVisitor(ocpp_paths=ocpp_paths,
                                                                          ocpp_module_id=self._ocpp_config.ocpp_module_id,
                                                                          ocpp_version=self._ocpp_config.ocpp_version)

        return occp_module_configuration_helper

    def _setup_libocpp_configuration(self, source_certs_directory: Path,
                                     temporary_paths: _EverestEnvironmentTemporaryPaths):

        liboccp_configuration_helper = LibOCPP16ConfigurationHelper() if self._ocpp_config.ocpp_version == OCPPVersion.ocpp16 else LibOCPP201ConfigurationHelper()

        if self._ocpp_config.template_ocpp_config:
            source_ocpp_config = self._ocpp_config.template_ocpp_config
        else:
            source_ocpp_config = self._determine_configured_charge_point_config_path_from_everest_config()

        liboccp_configuration_helper.install_default_ocpp_certificates(
            source_certs_directory=source_certs_directory,
            target_certs_directory=temporary_paths.certs_dir)  # Path(self.temp_ocpp_certs_dir.name))

        liboccp_configuration_helper.generate_ocpp_config(
            central_system_port=self._ocpp_config.central_system_port,
            source_ocpp_config_file=source_ocpp_config,
            target_ocpp_config_file=temporary_paths.ocpp_config_file,  # Path(self.temp_ocpp_config_file.name),
            target_ocpp_user_config_file=temporary_paths.ocpp_user_config_file,
            # Path(self.temp_ocpp_user_config_file.name),
        )

        if self._ocpp_config.ocpp_version == OCPPVersion.ocpp201:
            liboccp_configuration_helper.create_temporary_ocpp_configuration_db(
                libocpp_path=self._ocpp_config.libocpp_path,
                ocpp_configuration_file=temporary_paths.ocpp_config_file,
                target_directory=temporary_paths.ocpp_database_dir  # Path(self.temp_ocpp_database_dir.name),
            )

    def _create_everest_configuration_visitors(self, temporary_paths: _EverestEnvironmentTemporaryPaths):
        configuration_visitors = []
        if self._ocpp_config:
            configuration_visitors.append(self._create_ocpp_module_configuration_visitor(temporary_paths))
        if self._probe_config:
            configuration_visitors.append(
                ProbeModuleConfigurationVisitor(connections=self._probe_config.connections,
                                                module_id=self._probe_config.module_id))

        if self._evse_security_config and self._evse_security_config.use_temporary_certificates_folder:
            configuration_visitors.append(
                EvseSecurityModuleConfigurationVisitor(module_id=self._evse_security_config.module_id,
                                                       configuration=EvseSecurityModuleConfiguration.default_from_cert_path(
                                                           temporary_paths.certs_dir)))

        if self._persistent_store_config and self._persistent_store_config.use_temporary_folder:
            configuration_visitors.append(
                PersistentStoreConfigurationVisitor(sqlite_db_file_path=temporary_paths.persistent_store_db_path)
            )

        return configuration_visitors

    def _determine_configured_charge_point_config_path_from_everest_config(self):

        everest_template_config = yaml.safe_load(self._core_config.template_everest_config_path.read_text())

        charge_point_config_path = \
            everest_template_config["active_modules"][self._ocpp_config.ocpp_module_id]["config_module"][
                "ChargePointConfigPath"]

        if self._ocpp_config.ocpp_version == OCPPVersion.ocpp16:
            ocpp_dir = self._everest_core.prefix_path / "share/everest/modules/OCPP"
        elif self._ocpp_config.ocpp_version == OCPPVersion.ocpp201:
            ocpp_dir = self._everest_core.prefix_path / "share/everest/modules/OCPP201"
        else:
            raise ValueError(f"unknown OCPP version {self._ocpp_config.ocpp_version}")
        ocpp_config_path = ocpp_dir / charge_point_config_path
        return ocpp_config_path

    def _setup_evse_security_configuration(self, temporary_paths: _EverestEnvironmentTemporaryPaths):
        """ If configures, copies the source certificate trees"""
        if self._evse_security_config and self._evse_security_config.source_certificate_directory:
            shutil.copytree(self._evse_security_config.source_certificate_directory / "ca", temporary_paths.certs_dir / "ca", dirs_exist_ok=True)
            shutil.copytree(self._evse_security_config.source_certificate_directory / "client", temporary_paths.certs_dir / "client", dirs_exist_ok=True)
