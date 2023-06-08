from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import List

from . import ParsingException
from . import action, agent, formula, state, timepoint


@dataclass(slots=True)
class Statement(ABC):
    action: action.Action
    agent: agent.Agent
    precondition: formula.Formula

    @classmethod
    def from_ui(cls, data: dict) -> List[EffectStatement | ReleaseStatement]:
        try:
            _types = {
                "causes": EffectStatement,
                "releases": ReleaseStatement,
            }
            out = [
                _types[_data['statement_type']].from_ui(_data) for _data in data['STATEMENT']
            ]
        except (KeyError, ParsingException):
            raise ParsingException('Failed to parse statement.')
        return out

    def bool(self, obs: timepoint.Obs):
        return self.precondition.bool(obs=obs)


@dataclass(slots=True)
class EffectStatement(Statement):
    formula: formula.Formula
    postcondition: List[timepoint.Obs] = None

    def __post_init__(self):
        self.postcondition = self.formula.get_all_possibilities()

    @classmethod
    def from_ui(cls, data: dict):
        try:
            out = cls(
                action=action.Action(name=data['action']),
                agent=agent.Agent(name=data['agent']),
                precondition=formula.Formula.from_ui(data['condition']),
                formula=formula.Formula.from_ui(data['effects'])
            )
        except (KeyError, ParsingException):
            raise ParsingException('Failed to parse effect statement.')
        return out

@dataclass(slots=True)
class ReleaseStatement(Statement):
    postcondition: state.State

    @classmethod
    def from_ui(cls, data: dict):
        try:
            out = cls(
                action=action.Action(name=data['action']),
                agent=agent.Agent(name=data['agent']),
                precondition=formula.Formula.from_ui(data['condition']),
                postcondition=data['effects'][0]
            )
        except (KeyError, ParsingException):
            raise ParsingException('Failed to parse release statement.')
        return out