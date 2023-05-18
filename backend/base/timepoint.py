from __future__ import annotations

import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from dataclasses import dataclass
from typing import Optional, Tuple, List

from base.action import Action
from base.agent import Agent
from base.state import State

from base.exception import LogicException, ParsingException


@dataclass
class Obs(list):
    states: List[State]

    @classmethod
    def from_ui(cls, data: dict) -> Obs:
        try:
            _out = data['parsed_expression'][0]
            states = []
            for item in _out:
                if item == "and":
                    continue
                if isinstance(item, list):
                    states.append(State(name=item[1], holds=False))
                    continue
                states.append(State(name=item))
        except Exception:
            raise ParsingException('Failed to parse obs.')
        return cls(states=states)

    def __iter__(self):
        return list.__iter__(self.states)

    def __ior__(self, other) -> None:
        """validation state unique by name and holds

        Example:
        ---------------------------------------------
        >>> self |= other
        """

        update_tuples_nh = set(map(lambda x: (x.name, x.holds), other))
        update_tuples_n = set(map(lambda x: (x.name,), other))
        if len(update_tuples_nh) != len(update_tuples_n):
            raise LogicException('Scenario is not realizable - statement contains disjoint statements')

        _update = [State(name=name, holds=holds) for name, holds in update_tuples_nh]
    
        for update_element in _update:
            el = next(filter(lambda x: x.name == update_element.name, self), None)
            if el is None:
                raise LogicException("Not all states were defined in Obs.")

            el.holds = update_element.holds
        return self

    def get_by_name(self, name: str) -> Obs | None:
        _el = next(filter(lambda _state: _state.name == name, self.states), None)
        return _el


@dataclass(slots=True)
class TimePoint:
    t: int
    acs: Optional[Tuple[Action, Agent]] = None
    obs: Optional[Obs] = None

    @classmethod
    def from_ui(cls, data: dict) -> List[TimePoint]:
        try:
            out = [TimePoint(t=item['time'], acs=(Action(item['action']), Agent(name=item['agent']))) for item in data['ACS']]
            acs_t = list(map(lambda x: x.t, out))
            obs = [(item['time'], Obs.from_ui(item)) for item in data['OBS']]
            for _obs in obs:
                if _obs[0] in acs_t:
                    tp = next(filter(lambda x: x.t == _obs[0]))
                    tp.obs = _obs[1]
                else:
                    out.append(TimePoint(t=_obs[0], obs=_obs[1]))
        except KeyError:
            raise ParsingException('Failed to parse acs.')
        return out

    def is_acs(self):
        return self.acs is not None

    def is_obs(self):
        return self.obs is not None
