from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import ParsingException


@dataclass(slots=True)
class Agent:
    """ Class for Agent"""
    name: str
    active: bool = False

    @classmethod
    def from_ui(cls, data: dict) -> List[Agent]:
        try:
            out = [cls(name=_name) for _name in data['AGENT']]
        except KeyError:
            raise ParsingException('Failed to parse agent.')
        return out

    def __bool__(self):
        return self.active

    def __eq__(self, other) -> bool:
        return self.name == other.name
