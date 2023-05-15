from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import List

from . import action, agent, formula, state


@dataclass(slots=True)
class Statement(ABC):
    action: action.Action
    agent: agent.Agent
    precondition: formula.Formula

    def __bool__(self):
        return bool(self.precondition)


@dataclass(slots=True)
class EffectStatement(Statement):
    postcondition: List[state.State]


@dataclass(slots=True)
class ReleaseStatement(Statement):
    postcondition: List[state.State]
