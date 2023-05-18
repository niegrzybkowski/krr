from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

from . import action, agent, state
from . import LogicExpection, ParsingException


@dataclass
class Obs(list):
    states: List[state.State]

    @classmethod
    def from_ui(cls, data: dict) -> Obs:
        try:
            # TODO: change format to allow only `not`, `and` operators (like in effects)
            _out = data['parsed_expression'][0]
            states = []
            for item in _out:
                if item == "and":
                    continue
                if isinstance(item, list):
                    states.append(state.State(name=item[1], holds=False))
                    continue
                states.append(state.State(name=item))
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
            raise LogicExpection('Scenario is not realizable - statement contains disjoint statements')

        _update = [state.State(name=name, holds=holds) for name, holds in update_tuples_nh]
    
        for update_element in _update:
            print(other)
            print(self)
            el = next(filter(lambda x: x.name == update_element.name, self), None)
            if el is None:
                raise LogicExpection("Not all states were defined in Obs.")

            el.holds = update_element.holds
        return self


@dataclass(slots=True)
class TimePoint:
    t: int
    acs: Optional[Tuple[action.Action, agent.Agent]] = None
    obs: Optional[Obs] = None

    @classmethod
    def from_ui(cls, data: dict) -> List[TimePoint]:
        try:
            out = [TimePoint(t=item['time'], acs=(action.Action(item['action']), agent.Agent(name=item['agent']))) for item in data['ACS']]
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
