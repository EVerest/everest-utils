# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2023 Pionix GmbH and Contributors to EVerest

import os
import json
import shutil
from pathlib import Path
from paho.mqtt import client as mqtt_client
import logging
import yaml
import tempfile
import uuid

from everest.testing.ocpp_utils.controller.test_controller_interface import TestController
from everest.testing.core_utils.everest_core import EverestCore

logging.basicConfig(level=logging.DEBUG)


class EverestTestController(TestController):

    def __init__(self, everest_core_path, config_path: Path, chargepoint_id: str,
                 test_function_name: str = None) -> None:
        self.everest_core = EverestCore(everest_core_path, config_path)
        self.config_path = config_path
        self.mqtt_client = None
        self.chargepoint_id = chargepoint_id
        self.test_function_name = test_function_name
        self.temp_everest_config_file = tempfile.NamedTemporaryFile(delete=True, mode="w+", suffix=".yaml")
        self.temp_ocpp_config_file = tempfile.NamedTemporaryFile(delete=True, mode="w+", suffix=".json")
        self.temp_ocpp_user_config_file = tempfile.NamedTemporaryFile(delete=True, mode="w+", suffix=".json")
        self.temp_ocpp_database_dir = tempfile.TemporaryDirectory()
        self.temp_ocpp_log_dir = tempfile.TemporaryDirectory()
        self.mqtt_external_prefix = ""

    def start(self, central_system_port=None):
        logging.info(f"Central system port: {central_system_port}")
        # modify ocpp config with given central system port and modify everest-core config as well
        everest_config = yaml.safe_load(self.config_path.read_text())
        ocpp_dir = self.everest_core.everest_core_build_path / "dist/share/everest/ocpp"
        ocpp_config_path = ocpp_dir / everest_config["active_modules"]["charge_point"]["config_module"]["ChargePointConfigPath"]
        ocpp_config = json.loads(ocpp_config_path.read_text())
        charge_point_id = ocpp_config["Internal"]["ChargePointId"]
        ocpp_config["Internal"]["CentralSystemURI"] = f"127.0.0.1:{central_system_port}/{charge_point_id}"
        self.temp_ocpp_config_file.write(json.dumps(ocpp_config))
        self.temp_ocpp_config_file.flush()
        self.temp_ocpp_user_config_file.write(f"{{}}")
        self.temp_ocpp_user_config_file.flush()
        everest_config["active_modules"]["charge_point"]["config_module"]["ChargePointConfigPath"] = self.temp_ocpp_config_file.name
        everest_config["active_modules"]["charge_point"]["config_module"]["UserConfigPath"] = self.temp_ocpp_user_config_file.name
        everest_config["active_modules"]["charge_point"]["config_module"]["DatabasePath"] = self.temp_ocpp_database_dir.name
        everest_config["active_modules"]["charge_point"]["config_module"]["MessageLogPath"] = self.temp_ocpp_log_dir.name

        # namespace everest with uids
        everest_uuid = uuid.uuid4().hex
        self.mqtt_external_prefix = f"external_{everest_uuid}"
        everest_config["settings"] = {}
        everest_config["settings"]["mqtt_everest_prefix"] = f"everest_{everest_uuid}"
        everest_config["settings"]["mqtt_external_prefix"] = self.mqtt_external_prefix
        everest_config["settings"]["telemetry_prefix"] = f"telemetry_{everest_uuid}"

        # make sure controller starts with a dynamic port
        everest_config["settings"]["controller_port"] = 0

        yaml.dump(everest_config, self.temp_everest_config_file)

        self.config_path = Path(self.temp_everest_config_file.name)
        self.everest_core.everest_config_path = self.config_path
        self.everest_core.everest_core_user_config_path = Path(
            self.config_path.parent / 'config/user-config')
        self.everest_core.everest_core_user_config_path.mkdir(parents=True, exist_ok=True)

        logging.info(f"everest uuid: {everest_uuid}")
        logging.info(f"temp everest config: {self.config_path}")
        logging.info(f"temp everest user config: {self.everest_core.everest_core_user_config_path}")
        logging.info(f"temp ocpp config: {self.temp_ocpp_config_file.name}")
        logging.info(f"temp ocpp user config: {self.temp_ocpp_user_config_file.name}")

        # FIXME: this is the everest config, not the ocpp config being copied...
        # self.copy_occp_config()
        self.everest_core.start(None)

        mqtt_server_uri = os.environ.get("MQTT_SERVER_ADDRESS", "127.0.0.1")
        mqtt_server_port = int(os.environ.get("MQTT_SERVER_PORT", "1883"))

        self.mqtt_client = mqtt_client.Client(everest_uuid)
        self.mqtt_client.connect(mqtt_server_uri, mqtt_server_port)

        self.mqtt_client.publish(
            f"{self.mqtt_external_prefix}everest_external/nodered/1/carsim/cmd/enable", "true")
        self.mqtt_client.publish(
            f"{self.mqtt_external_prefix}everest_external/nodered/2/carsim/cmd/enable", "true")

    def stop(self):
        self.everest_core.stop()

    def plug_in(self, connector_id=1):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_external/nodered/{connector_id}/carsim/cmd/execute_charging_session",
                                 "sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 32,1;sleep 200;unplug")

    def plug_in_ac_iso(self, payment_type='contract', connector_id=1):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_external/nodered/{connector_id}/carsim/cmd/execute_charging_session",
                                 f"sleep 1;iso_wait_slac_matched;iso_start_v2g_session {payment_type},AC_three_phase_core;iso_wait_pwr_ready;iso_draw_power_regulated 16,3;sleep 20;iso_stop_charging;iso_wait_v2g_session_stopped;unplug")

    def plug_out(self, connector_id=1):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_external/nodered/{connector_id}/carsim/cmd/modify_charging_session",
                                 "unplug")

    def swipe(self, token, connectors=[1]):
        provided_token = {
            "id_token": token,
            "type": "RFID",
            "connectors": connectors
        }
        self.mqtt_client.publish(
            f"{self.mqtt_external_prefix}everest_api/dummy_token_provider/cmd/provide", json.dumps(provided_token))

    def connect_websocket(self):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_api/ocpp/cmd/connect", "on")

    def disconnect_websocket(self):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_api/ocpp/cmd/disconnect", "off")

    def rcd_error(self, connector_id=1):
        self.mqtt_client.publish(f"{self.mqtt_external_prefix}everest_external/nodered/{connector_id}/carsim/cmd/execute_charging_session",
                                 "sleep 1;rcd_current 10.3;sleep 10;rcd_current 0.1;unplug")

    def publish(self, topic, payload):
        self.mqtt_client.publish(topic, payload)

    def copy_occp_config(self):
        ocpp_dir = self.everest_core.everest_core_build_path / "dist/share/everest/ocpp"
        dest_file = os.path.join(ocpp_dir, self.config_path.name)
        shutil.copy(self.config_path, dest_file)
