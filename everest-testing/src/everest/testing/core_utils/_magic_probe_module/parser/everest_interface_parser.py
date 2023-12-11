from pathlib import Path
from typing import Any

import yaml

from ..types.json_schema_models import SCHEMAS_BY_TYPE, JsonSchema, StringJsonSchema
from ..types.everest_command import EverestCommand
from ..types.everest_interface import EverestInterface
from ..types import everest_interface_schema
from ..types.everest_variable import EverestVariable


class EverestInterfaceParser:

    def __init__(self):
        pass

    def _parse_file(self, file: Path) -> EverestInterface:
        with file.open("r") as f:
            interface_schema = everest_interface_schema.EverestInterfaceSchema(**yaml.safe_load(f))
        commands = {}
        for command_name, command_def in interface_schema.cmds.items():
            commands[command_name] = self._parse_command(command_name, command_def)

        variables = {}
        for var_name, _ in interface_schema.vars.items():
            variables[var_name] = EverestVariable(name=var_name)

        return EverestInterface(file.stem,
                                commands=commands,
                                variables=variables)

    def parse(self, interface_directories: list[Path]) -> list[EverestInterface]:
        interfaces = [self._parse_file(file) for interface_dir in interface_directories
                      for file in interface_dir.glob("*.yaml")]

        return interfaces

    def _parse_command(self, name: str, command_schema: everest_interface_schema.Cmds) -> EverestCommand:
        if command_schema.arguments:
            args = {arg_name: self._parse_argument_schema(arg_schema.model_dump()) for arg_name, arg_schema in
                    command_schema.arguments.root.items()}
        else:
            args = {}

        return EverestCommand(
            name=name,
            arguments=args,
            result=self._parse_argument_schema(command_schema.result.model_dump()) if command_schema.result else None
        )

    @staticmethod
    def _parse_argument_schema(schema: dict) -> JsonSchema:
        if isinstance(schema.get("type", "object"), list):
            # unspecified -> choose string
            if "string" in schema["type"]:
                return StringJsonSchema(type="string")
            else:
                raise NotImplementedError
        s = SCHEMAS_BY_TYPE[schema.get("type", "object")]
        return s(**schema)
