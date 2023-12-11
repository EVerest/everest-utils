import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from ..types.json_schema_models import SCHEMAS_BY_TYPE
from ..types.everest_type import EverestType


class EverestTypeParser:

    def _parse_type_file(self, type_file: Path):
        parsed_types = {}
        with type_file.open("r") as f:
            schema = yaml.safe_load(f)
            for name, type_schema in schema["types"].items():
                s = SCHEMAS_BY_TYPE[type_schema.get("type", "object")]
                try:
                    schema = s(**type_schema)
                    ref = f"/{type_file.stem}#/{name}"

                    parsed_types[ref] = EverestType(name=name,
                                                    namespace=type_file.stem,
                                                    json_ref=ref,
                                                    json_schema=schema)

                except ValidationError as e:
                    logging.error(f"failed to parse {name} in {type_file}")
                    raise e
        return parsed_types

    def parse(self, type_files: list[Path]) -> dict[str, EverestType]:
        parsed_types = {}

        for file in type_files:
            parsed_types.update(self._parse_type_file(file))

        return parsed_types
