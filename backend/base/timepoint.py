from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

from . import action, agent, state, formula
from . import LogicException, ParsingException


@dataclass(slots=True)
class Obs(list):
    states: List[state.State] = None
    formula: formula.Formula = None

    def get_all_possibilities(self) -> List[Obs]:
        return self.formula.get_all_possibilities()

    @classmethod
    def from_ui(cls, data: dict) -> Obs:
        try:
            out = cls(
                formula=formula.Formula.from_ui(data['parsed_expression'])
            )
        except Exception:
            raise ParsingException('Failed to parse obs.')
        return out

    def is_superset(self, other: Obs) -> bool:
        for _state in self.states:
            if _state not in other.states:
                return False
        return True

    def get_state_by_name(self, name):
        return next(filter(lambda _state: _state.name == name, self.states))

    def __iter__(self):
        return list.__iter__(self.states)

    def __ior__(self, other) -> Obs:
        """validation state unique by name and holds

        Example:
        ---------------------------------------------
        >>> self |= other
        """

        update_tuples_nh = set(map(lambda x: (x.name, x.holds), other))
        update_tuples_n = set(map(lambda x: (x.name,), other))
        if len(update_tuples_nh) != len(update_tuples_n):
            raise LogicException('Scenario is not realizable - statement contains disjoint statements')

        _update = [state.State(name=name, holds=holds) for name, holds in update_tuples_nh]

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
    acs: Optional[Tuple[action.Action, agent.Agent]] = None
    obs: Optional[Obs] = None

    @classmethod
    def from_ui(cls, data: dict) -> List[TimePoint]:
        try:
            out = [TimePoint(t=item['time'], acs=(action.Action(item['action']), agent.Agent(name=item['agent']))) for
                   item in data['ACS']]
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
