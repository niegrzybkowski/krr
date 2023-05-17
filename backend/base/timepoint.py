from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

from . import action, agent, state
from ..exceptions import LogicExpection


@dataclass
class Obs:
    states: List[state.State]

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
            el = next(filter(lambda x: x.name == update_element.name, self))

            el.holds = update_element.holds
        return self


@dataclass(slots=True)
class TimePoint:
    t: int
    acs: Optional[Tuple[action.Action, agent.Agent]] = None
    obs: Optional[Obs] = None

    def is_acs(self):
        return self.acs is not None

    def is_obs(self):
        return self.obs is not None
