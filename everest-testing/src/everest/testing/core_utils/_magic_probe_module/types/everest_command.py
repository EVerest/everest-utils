from dataclasses import dataclass

from ..types.json_schema_models import JsonSchema


@dataclass(frozen=True)
class EverestCommand:
    name: str
    arguments: dict[str, JsonSchema]
    result: JsonSchema | None = None
