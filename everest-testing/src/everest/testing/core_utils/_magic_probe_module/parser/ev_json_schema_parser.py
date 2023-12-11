import logging
from dataclasses import dataclass
from pathlib import Path

import yaml
from ev_cli.ev import load_interface_definition, generate_tmpl_data_for_if
from pydantic import ValidationError

from everest_smoke_tests.parser.ev_cli_parsed_type_schemas import EvCliParsedInterfaceTemplateData, \
    EvCliParsedInterfaceDefinition
from everest_smoke_tests.parser.json_schema_models import SCHEMAS_BY_TYPE
from everest_smoke_tests.types.everest_type import EverestType


@dataclass
class EvCliParsedInterface:
    interface: str
    ev_cli_interface_def: EvCliParsedInterfaceDefinition
    ev_cli_template_data: EvCliParsedInterfaceTemplateData


class EvJsonSchemaParser:
    def __init__(self, everest_directories: list[Path]):
        """
        :param schemas_dir: Directory of EVerest framework's YAML schemas
        :param everest_directories: List of EVerest directories containing "interfaces" or "types" folders
        """
        self._everest_directories = everest_directories
        self._parsed_types = None
        self._parsed_interfaces = None





    # def scan_everest_directories_for_interfaces(self, everest_directories: list[Path]) -> list[str]:
    #     interfaces = []
    #     for everest_dir in self._everest_directories:
    #         interface_dir = everest_dir / 'interfaces'
    #         interfaces += [if_path.stem for if_path in interface_dir.glob("*.yaml")]
    #     return interfaces

    # def _parse_interfaces(self):
    #     self._setup_ev_cli()
    #     self._parsed_interfaces = [
    #         self._parse_interface(interface) for interface in self._scan_everest_directories_for_interfaces()
    #     ]

    # def _parse_interface(self, interface: str):
    #     # if_parts = {'base': None, 'exports': None, 'types': None}
    #
    #     # try:
    #
    #     if_def, _ = load_interface_definition(interface)
    #     # except Exception as e:
    #     #     if not all_interfaces_flag:
    #     #         raise
    #     #     else:
    #     #         # FIXME (aw): should we really silently ignore that?
    #     #         print(f'Ignoring interface {interface} with reason: {e}')
    #     #         return
    #
    #     tmpl_data = generate_tmpl_data_for_if(interface, if_def, False)
    #     try:
    #         return EvCliParsedInterface(interface=interface,
    #                                     ev_cli_interface_def=EvCliParsedInterfaceDefinition(**if_def),
    #                                     ev_cli_template_data=EvCliParsedInterfaceTemplateData(**tmpl_data))
    #     except ValidationError as e:
    #         logging.error(f"Failed to parse interface {interface}")
    #         raise e
