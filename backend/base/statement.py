from __future__ import annotations

import itertools
from abc import ABC
from dataclasses import dataclass
from typing import List

from . import action, agent, formula, state, timepoint
from . import ParsingException


def getPrecondition(value):
    return value


def getPostcondition(value: List[str]) -> List[state.State]:
    holds = True
    out = []
    for el in value:
        if el == "not":
            holds = False
            continue
        out.append(state.State(name=el, holds=holds))
        holds = True
    return out


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
                _types[_data['statement_type']](
                    action=action.Action(name=_data['action']),
                    agent=agent.Agent(name=_data['agent']),
                    precondition=formula.Formula.from_ui(_data),
                    postcondition=getPostcondition(_data['effects'])
                ) for _data in data['STATEMENT']
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


@dataclass(slots=True)
class ReleaseStatement(Statement):
    postcondition: state.State
