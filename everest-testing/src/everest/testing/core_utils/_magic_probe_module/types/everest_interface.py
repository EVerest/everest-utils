from dataclasses import dataclass

from ..types.everest_command import EverestCommand
from ..types.everest_variable import EverestVariable


@dataclass(frozen=True)
class EverestInterface:
    interface: str
    commands: dict[str, EverestCommand]
    variables: dict[str, EverestVariable]
