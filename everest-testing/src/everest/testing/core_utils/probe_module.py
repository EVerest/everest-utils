import asyncio
import logging
from queue import Queue
from typing import Any, Callable

from everest.framework import Module, RuntimeSession


class ProbeModule:

    def __init__(self, session: RuntimeSession, connection_vars=None):
        self._connection_vars = {} if not connection_vars else connection_vars
        logging.info("ProbeModule init start")
        m = Module('probe', session)
        self._setup = m.say_hello()
        self._mod = m

        # subscribe to session events
        logging.info(self._setup.connections)

        self._message_queues = {connection: {var_name: Queue() for var_name in variable_names}
                                for connection, variable_names in self._connection_vars.items()
                                }
        for connection, variable_names in self._connection_vars.items():
            for variable_name in variable_names:
                self._mod.subscribe_variable(self._setup.connections[connection][0], variable_name,
                                             lambda message, _variable_name=variable_name,
                                                    _connection=connection: self._handle_subscribed_message(
                                                 queue=self._message_queues[_connection][_variable_name],
                                                 message=message,
                                                 variable_name=_variable_name,
                                                 connection=_connection))
        self._ready_event = asyncio.Event()
        m.init_done(self._ready)
        logging.info("ProbeModule init done")

    def _ready(self):
        logging.info("ProbeModule ready")
        self._ready_event.set()

    # handlers for receiving publications
    @staticmethod
    def _handle_subscribed_message(queue, message, connection, variable_name):
        queue.put(message)
        logging.info(f"Got {connection} - {variable_name}: {message}!")

    def get_queue(self, connection: str, variable_name: str):
        return self._message_queues[connection][variable_name]

    def call_command(self, interface_name: str, command_name: str, args: dict) -> Any:
        interface = self._setup.connections[interface_name][0]
        try:
            return self._mod.call_command(interface, command_name, args)
        except Exception as e:
            logging.info(f"Exception in calling command {command_name}: {type(e)}: {e}")
            raise e

    def publish_variable(self, implementation_id: str, variable_name: str, value: dict | str):
        self._mod.publish_variable(implementation_id, variable_name, value)

    def implement_command(self, implementation_id: str, command_name: str,
                          handler: Callable[[dict], dict]):
        self._mod.implement_command(implementation_id, command_name, handler)

    async def wait_to_be_ready(self, timeout=3):
        await asyncio.wait_for(self._ready_event.wait(), timeout)
