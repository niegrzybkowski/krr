from __future__ import annotations

from copy import deepcopy as copy
from dataclasses import dataclass
from typing import List

from . import ParsingException
from . import timepoint as tp, statement as st, state as state, formula, exception as exc


@dataclass(slots=True)
class Action:
    name: str

    @classmethod
    def from_ui(cls, data: dict) -> List[Action]:
        try:
            out = [cls(name=_name) for _name in data['ACTION']]
        except KeyError:
            raise ParsingException('Failed to parse action.')
        return out

    def run(
            self, obs: tp.Obs, statements: List[st.Statement]
    ) -> List[tp.Obs]:
        """run action by agent if """
        causes_satisfied: int = 0
        causes_structure = []

        for _statement in filter(lambda x: isinstance(x, st.EffectStatement), statements):
            if _statement.precondition.bool(obs=obs):
                causes_satisfied += 1
                if causes_satisfied <= 1:
                    causes_structure.append(_statement.formula.structure)
                else:
                    causes_structure.extend(["and", _statement.formula.structure])

        postconditions: List[List[state.State]] = [possibility.states for possibility in
                                                   formula.Formula(causes_structure).get_all_possibilities()]

        for _statement in filter(lambda x: isinstance(x, st.ReleaseStatement), statements):
            if _statement.precondition.bool(obs=obs):
                if postconditions:
                    psc: List[List[state.State]] = []
                    old_postconditions = copy(postconditions)
                    postconditions = []
                    for postcondition in old_postconditions:
                        if _statement.postcondition in postcondition:
                            continue
                        temp = copy(postcondition)
                        temp2 = copy(postcondition)
                        temp.append(state.State(_statement.postcondition.name, False))
                        temp2.append(state.State(_statement.postcondition.name, True))
                        psc.extend([temp, temp2])
                    postconditions.extend(psc)
                else:
                    psc = _statement.postcondition
                    psc2 = state.State(name=psc.name, holds=not psc.holds)
                    postconditions.extend([[psc], [psc2]])

        new_obs = []
        for postcondition in postconditions:
            # update states with all postconditions that can be applied
            temp = tp.Obs(states=copy(obs.states))
            temp |= tp.Obs(states=postcondition)
            new_obs.append(temp)

        return new_obs

    def __eq__(self, other: Action) -> bool:
        return self.name == other.name
