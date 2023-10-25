# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2023 Pionix GmbH and Contributors to EVerest
import sys
import os
from functools import wraps
from unittest.mock import Mock

import pytest
import tempfile
import pytest_asyncio
import shutil
import ssl
import socket
from threading import Thread
import getpass
from pathlib import Path

from everest.testing.ocpp_utils.charge_point_v201 import ChargePoint201
from ocpp.routing import on
from pyftpdlib import servers
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler

from everest.testing.core_utils.configuration.everest_environment_setup import EverestEnvironmentOCPPConfiguration
from everest.testing.core_utils.controller.everest_test_controller import EverestTestController
from everest.testing.ocpp_utils.central_system import CentralSystem
from everest.testing.ocpp_utils.charge_point_utils import TestUtility, OcppTestConfiguration

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))


@pytest.fixture
def ocpp_config(request, test_config: OcppTestConfiguration):
    ocpp_version = request.node.get_closest_marker("ocpp_version")
    if ocpp_version:
        ocpp_version = request.node.get_closest_marker("ocpp_version").args[0]
    else:
        ocpp_version = "ocpp1.6"

    ocpp_config_marker = request.node.get_closest_marker("ocpp_config")

    return EverestEnvironmentOCPPConfiguration(
        central_system_port=test_config.csms_port,
        ocpp_version=ocpp_version,
        libocpp_path=Path(request.config.getoption("--libocpp")),
        template_ocpp_config=Path(ocpp_config_marker) if ocpp_config_marker else None
    )



@pytest_asyncio.fixture
async def central_system_v16(request, test_config: OcppTestConfiguration):
    """Fixture for CentralSystem. Can be started as TLS or
    plain websocket depending on the request parameter.
    """

    if (hasattr(request, 'param')):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(test_config.certificate_info.csms_cert,
                                    test_config.certificate_info.csms_key,
                                    test_config.certificate_info.csms_passphrase)
    else:
        ssl_context = None
    cs = CentralSystem(test_config.csms_port,
                       test_config.charge_point_info.charge_point_id,
                       ocpp_version='ocpp1.6')
    await cs.start(ssl_context)
    yield cs

    await cs.stop()




def _incject_csms_v201_mock(cs: CentralSystem) -> Mock:
    """ Given a not yet started CentralSystem, add mock overrides for _any_ action handler.

    If not touched, those will simply proxy any request.

    However, they allow later change of the CSMS return values:

    Example:

    """
    def catch_mock(mock, method_name, method):
        method_mock = getattr(mock, method_name)

        @on(method._on_action)
        @wraps(method)
        def _method(*args, **kwargs):
            mock_res = method_mock(*args, **kwargs)
            if method_mock.side_effect:
                return mock_res
            return method(cs.chargepoint, *args, **kwargs)
        return _method
    mock = Mock(spec=ChargePoint201)
    charge_point_action_handlers = {k:v for k,v  in ChargePoint201.__dict__.items() if hasattr(v, "_on_action")}
    for action_name, action_method in charge_point_action_handlers.items():
        cs.function_overrides.append( (action_name, catch_mock(mock, action_name, action_method)))
    return mock


@pytest_asyncio.fixture
async def central_system_v201(request, test_config: OcppTestConfiguration):
    """Fixture for CentralSystem. Can be started as TLS or
    plain websocket depending on the request parameter.
    """
    if (hasattr(request, 'param')):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(test_config.certificate_info.csms_cert,
                                    test_config.certificate_info.csms_key,
                                    test_config.certificate_info.csms_passphrase)
    else:
        ssl_context = None
    cs = CentralSystem(test_config.csms_port,
                       test_config.charge_point_info.charge_point_id,
                       ocpp_version='ocpp2.0.1')

    if request.node.get_closest_marker('inject_csms_mock'):
        mock = _incject_csms_v201_mock(cs)
        cs.mock = mock

    await cs.start(ssl_context)
    yield cs

    await cs.stop()


@pytest_asyncio.fixture
async def central_system_v16_standalone(request, central_system_v16: CentralSystem, test_controller: EverestTestController):
    """Fixture for standalone central system. Requires central_system_v16 and test_controller. Starts test_controller immediately
    """
    test_controller.start()
    yield central_system_v16


@pytest_asyncio.fixture
async def charge_point_v16(request, central_system_v16: CentralSystem, test_controller: EverestTestController):
    """Fixture for ChargePoint16. Requires central_system_v16 and test_controller. Starts test_controller immediately
    """
    marker = request.node.get_closest_marker('standalone_module')
    if marker is None:
        test_controller.start() # standalone_module = self._probe_config.module_id
    else:
        raise Exception("Using a standalone module with the charge_point_v16 fixture is not supported, please use central_system_v16_standalone")
    cp = await central_system_v16.wait_for_chargepoint()
    yield cp
    cp.stop()



@pytest_asyncio.fixture
async def charge_point_v201(central_system_v201: CentralSystem, test_controller: EverestTestController):
    """Fixture for ChargePoint16. Requires central_system_v201 and test_controller. Starts test_controller immediately
    """
    test_controller.start()
    cp = await central_system_v201.wait_for_chargepoint()
    yield cp
    cp.stop()


@pytest.fixture
def test_utility():
    """Fixture for test case meta data
    """
    return TestUtility()

@pytest.fixture
def test_config():
    return OcppTestConfiguration()

class FtpThread(Thread):
    def set_port(self, port):
        self.port = port


@pytest.fixture
def ftp_server(test_config: OcppTestConfiguration):
    """This fixture creates a temporary directory and starts
    a local ftp server connected to that directory. The temporary
    directory is deleted afterwards
    """

    d = tempfile.mkdtemp(prefix='tmp_ftp')
    address = ("127.0.0.1", 0)
    ftp_socket = socket.socket()
    ftp_socket.bind(address)
    port = ftp_socket.getsockname()[1]

    def _ftp_server(test_config: OcppTestConfiguration, ftp_socket):

        shutil.copyfile(test_config.firmware_info.update_file, os.path.join(
            d, "firmware_update.pnx"))
        shutil.copyfile(test_config.firmware_info.update_file_signature,
                        os.path.join(d, "firmware_update.pnx.base64"))

        authorizer = DummyAuthorizer()
        authorizer.add_user(getpass.getuser(), "12345", d, perm="elradfmwMT")

        handler = FTPHandler
        handler.authorizer = authorizer

        server = servers.FTPServer(ftp_socket, handler)

        server.serve_forever()

    ftp_thread = FtpThread(target=_ftp_server, args=[test_config, ftp_socket])
    ftp_thread.daemon = True
    ftp_thread.set_port(port)
    ftp_thread.start()

    yield ftp_thread

    shutil.rmtree(d)
