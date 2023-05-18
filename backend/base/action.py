from __future__ import annotations

import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from copy import deepcopy as copy
from dataclasses import dataclass
from typing import List

from base.agent import Agent
from base.statement import Statement, EffectStatement, ReleaseStatement
import base.timepoint
from base.exception import ParsingException


@dataclass(slots=True)
class Action:
    name: str
    performed: bool = False

    @classmethod
    def from_ui(cls, data: dict) -> List[Action]:
        try:
            out = [cls(name=_name) for _name in data['ACTION']]
        except KeyError:
            raise ParsingException('Failed to parse action.')
        return out

    def run(
            self, agent: Agent, obs: base.timepoint.Obs, statements: List[Statement]
    ) -> List[base.timepoint.Obs]:
        """run action by agent if """
        postconditions = [[]]
        for _statement in filter(lambda x: isinstance(x, EffectStatement), statements):
            if _statement.precondition.bool(obs=obs):
                agent.active = True
                self.performed = True
                postconditions[0].extend(copy(_statement.postcondition))

        for _statement in filter(lambda x: isinstance(x, ReleaseStatement), statements):
            if _statement.precondition.bool(obs=obs):
                agent.active = True
                self.performed = True

                psc = []
                psc2 = []
                for postcondition in postconditions:
                    temp = copy(postcondition)
                    temp.extend(copy(_statement.postcondition))
                    psc2.append(temp)
                    psc.append(copy(postcondition))

                postconditions.extend(psc)
                postconditions.extend(psc2)

        new_obs = []
        for postcondition in postconditions:
            # update states with all postconditions that can be applied
            temp = base.timepoint.Obs(states=copy(obs.states))
            temp |= base.timepoint.Obs(states=postcondition)
            new_obs.append(temp)

        return new_obs

    def __eq__(self, other: Action) -> bool:
        return self.name == other.name

    def __bool__(self) -> bool:
        return self.performed
