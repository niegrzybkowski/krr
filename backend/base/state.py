from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import ParsingException


@dataclass(slots=True)
class State:
    name: str
    holds: bool = True

    @classmethod
    def from_ui(cls, data: dict) -> List[State]:
        try:
            out = [cls(name=_name) for _name in data['STATE']]
        except KeyError:
            raise ParsingException('Failed to parse state.')
        return out

    def __bool__(self) -> bool:
        return self.holds
