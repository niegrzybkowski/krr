from __future__ import annotations

import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from abc import ABC
from dataclasses import dataclass
from typing import List

import  base.action
import  base.agent
import  base.formula
import  base.state
import  base.timepoint
from base.exception import ParsingException


def getPrecondition(value):
    return value

def getPostcondition(value: List[str]) -> List[base.state.State]:
    holds = True
    out = []
    for el in value:
        if el == "not":
            holds = False
            continue
        out.append(base.state.State(name=el, holds=holds))
        holds = True
    return out


@dataclass(slots=True)
class Statement(ABC):
    action: base.action.Action
    agent: base.agent.Agent
    precondition: base.formula.Formula

    @classmethod
    def from_ui(cls, data: dict) -> List[EffectStatement | ReleaseStatement]:
        try:
            _types = {
                "causes": EffectStatement,
                "releases": ReleaseStatement,
            }
            out = [
                _types[_data['statement_type']](
                    action=base.action.Action(name=_data['action']),
                    agent=base.agent.Agent(name=_data['agent']),
                    precondition=base.formula.Formula.from_ui(_data),
                    postcondition=getPostcondition(_data['effects'])
                    ) for _data in data['STATEMENT']
                ]
        except (KeyError, ParsingException):
            raise ParsingException('Failed to parse statement.')
        return out

    def bool(self, obs: base.timepoint.Obs):
        return self.precondition.bool(obs=obs)


@dataclass(slots=True)
class EffectStatement(Statement):
    postcondition: List[base.state.State]


@dataclass(slots=True)
class ReleaseStatement(Statement):
    postcondition: List[base.state.State]
