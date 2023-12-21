import logging
from typing import Callable, Any
from unittest.mock import Mock

from everest.testing.core_utils.common import Requirement
from everest.testing.core_utils.probe_module import ProbeModule, RuntimeSession

from .types.everest_command import EverestCommand
from .types.everest_interface import EverestInterface
from .types.everest_type import EverestType
from .value_generator import ValueGenerator

class MagicProbeModule(ProbeModule):

    def __init__(self,
                 interface_implementations: dict[str, EverestInterface],
                 types: list[EverestType],
                 connections: dict[str, list[tuple[Requirement, EverestInterface]]],
                 session: RuntimeSession,
                 strict_mode: bool = False, module_id="probe"):
        """

        Args:
            interface_implementations: implemented interfaces of the probe module, indexed by implementation_id
            types: parsed EverestTypes (required for value generation)
            connections: connections of the Probe Module (i.e. fulfilled by other modules)
            strict_mode: if True, exceptions are raised for not-implemented commands
            session:
            module_id:
        """
        self._strict_mode = strict_mode
        self._interface_implementations = interface_implementations
        self._connections = connections
        super().__init__(session, module_id)
        self._value_generator = ValueGenerator(types)
        self._implementation_mocks: dict[str, Mock] = {}
        self._init_commands()

    def implement_command(self, implementation_id: str, command_name: str, handler: Callable[[dict], Any]):
        getattr(self._implementation_mocks[implementation_id], command_name).side_effect = handler

    def get_interface_implementations(self) -> dict[str, EverestInterface]:
        """

        Returns: Mapping implementation id -> EverestInterface of all implemented interfaces by the probe module

        """
        return self._interface_implementations

    def publish_on_all_interface_implementations(self, interface_name: str, variable: str, value: Any):
        implementations = [k for k,v in self._interface_implementations.items() if v.interface == interface_name]
        for implementation in implementations:
            super().publish_variable(implementation, variable, value)

    def subscribe_all(self,
                      message_callback: Callable[[Any], None],
                      module_filter: Callable[[str], bool] | None = None,
                      implementation_id_filter: Callable[[str], bool] | None = None,
                      interface_filter: Callable[[str], bool] | None = None,
                      variable_filter: Callable[[str], bool] | None = None):
        """ Subscribes to _all_ connections (possibly filtered) """

        for module_id, module_connections in self._connections.items():
            if not module_filter or module_filter(module_id):
                for requirement, interface in module_connections:
                    if (not implementation_id_filter or implementation_id_filter(requirement.implementation_id)) and \
                            (not interface_filter or interface_filter(interface.interface)):
                        for variable in interface.variables:
                            if not variable_filter or variable_filter(variable):
                                super().subscribe_variable(module_id, variable, message_callback)

    @property
    def implementation_mocks(self) -> dict[str, Mock]:
        return self._implementation_mocks

    def _init_commands(self):
        for implementation_id, interface in self._interface_implementations.items():
            for command in interface.commands.values():
                self._init_command(implementation_id, command)

    def _init_command(self, implementation_id: str, command: EverestCommand):
        super().implement_command(
            implementation_id=implementation_id,
            command_name=command.name,
            handler=self._create_command_handler(implementation_id, command)
        )

    def _create_command_handler(self, implementation_id: str, command: EverestCommand):
        command_mock = getattr(self._implementation_mocks.setdefault(implementation_id, Mock()), command.name)
        original_return_value = command_mock.return_value

        def _handler(*args, **kwargs):
            res = command_mock(*args, **kwargs)
            if command_mock.side_effect or command_mock.return_value != original_return_value:
                return res
            elif command.result:
                if self._strict_mode:
                    raise NotImplementedError(f"MagicProbeModule command {implementation_id} / {command} not implemented")
                logging.warning(f"MagicProbeModule command {implementation_id} / {command} not implemented - returning auto-generated value!")
                return self._value_generator.generate(command.result)
            else:
                return None

        return _handler
