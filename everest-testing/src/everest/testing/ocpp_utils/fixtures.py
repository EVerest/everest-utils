# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2023 Pionix GmbH and Contributors to EVerest

import sys
import os
import pytest
import tempfile
import pytest_asyncio
import shutil
import asyncio
import ssl
import socket
from threading import Thread
import getpass
from enum import Enum
from pathlib import Path
from pyftpdlib import servers
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from everest.testing.ocpp_utils.controller.test_controller_interface import TestController
from everest.testing.ocpp_utils.controller.everest_test_controller import EverestTestController
from everest.testing.ocpp_utils.central_system import CentralSystem
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

class ValidationMode(str, Enum):
    STRICT = "STRICT"
    EASY = "EASY"


class TestUtility:
    def __init__(self) -> None:
        self.messages = []
        self.validation_mode = ValidationMode.EASY
        self.forbidden_actions = []


@pytest.fixture
def test_controller(request, test_config) -> TestController:
    """Fixture that references the the test_controller that can be used for
    control events for the test cases.
    """
    everest_core_path = Path(request.config.getoption("--path"))
    config_path = test_config['ConfigPath']
    test_controller = EverestTestController(
        everest_core_path, config_path, test_config['ChargePoint']['ChargePointId'], request.function.__name__)
    yield test_controller
    test_controller.stop()


@pytest_asyncio.fixture
async def central_system_v16(request, test_config):
    """Fixture for CentralSystem. Can be started as TLS or
    plain websocket depending on the request parameter.
    """

    if (hasattr(request, 'param')):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(Path(test_config['Certificates']['CSMS']),
                                    Path(test_config['Certificates']['CSMSKey']),
                                    test_config['Certificates']['CSMSPassphrase'])
    else:
        ssl_context = None
    cs = CentralSystem(None,
                       test_config['ChargePoint']['ChargePointId'],
                       ocpp_version='ocpp1.6')
    await cs.start(ssl_context)
    yield cs

    await cs.stop()


@pytest_asyncio.fixture
async def central_system_v201(request, test_config):
    """Fixture for CentralSystem. Can be started as TLS or
    plain websocket depending on the request parameter.
    """
    if (hasattr(request, 'param')):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(Path(test_config['Certificates']['CSMS']),
                                    Path(test_config['Certificates']['CSMSKey']),
                                    Path(test_config['Certificates']['CSMSKey']),
                                    test_config['Certificates']['CSMSPassphrase'])
    else:
        ssl_context = None
    cs = CentralSystem(test_config['CSMS']['Port'],
                       test_config['ChargePoint']['ChargePointId'],
                       ocpp_version='ocpp2.0.1')
    await cs.start(ssl_context)
    yield cs

    await cs.stop()


@pytest_asyncio.fixture
async def charge_point_v16(central_system_v16: CentralSystem, test_controller: TestController):
    """Fixture for ChargePoint16. Requires central_system_v16 and test_controller. Starts test_controller immediately
    """
    test_controller.start(central_system_v16.port)
    cp = await central_system_v16.wait_for_chargepoint()
    yield cp
    cp.stop()


@pytest_asyncio.fixture
async def charge_point_v201(central_system_v201: CentralSystem, test_controller: TestController):
    """Fixture for ChargePoint16. Requires central_system_v201 and test_controller. Starts test_controller immediately
    """
    test_controller.start()
    await asyncio.sleep(1)
    cp = await central_system_v201.wait_for_chargepoint()
    yield cp
    cp.stop()


@pytest.fixture
def test_utility():
    """Fixture for test case meta data
    """
    return TestUtility()


class FtpThread(Thread):
    def set_port(self, port):
        self.port = port

@pytest.fixture
def ftp_server(test_config):
    """This fixture creates a temporary directory and starts
    a local ftp server connected to that directory. The temporary
    directory is deleted afterwards
    """

    d = tempfile.mkdtemp(prefix='tmp_ftp')
    address = ("127.0.0.1", 0)
    ftp_socket = socket.socket()
    ftp_socket.bind(address)
    port = ftp_socket.getsockname()[1]

    def _ftp_server(test_config, ftp_socket):
        test_controller_name = test_config['TestController']

        if test_controller_name == 'EVerest':
            shutil.copyfile(test_config['Firmware']['UpdateFile'], os.path.join(d, "firmware_update.pnx"))
            shutil.copyfile(test_config['Firmware']['UpdateFileSignature'],
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
