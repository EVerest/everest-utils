from abc import ABC
from dataclasses import dataclass

from ..types.json_schema_models import JsonSchema


@dataclass(frozen=True)
class EverestType(ABC):
    name: str
    namespace: str
    json_schema: JsonSchema
    json_ref: str



