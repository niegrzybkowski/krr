from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sortedcontainers import SortedDict

from . import LogicException, ParsingException
from . import Statement, TimePoint, Obs, State
from .formula import _get_all_possibilities


@dataclass(slots=True)
class Scenario:
    statements: List[Statement]
    timepoints: SortedDict[int, TimePoint] = field(default_factory=SortedDict)

    @classmethod
    def from_timepoints(cls, timepoints: List[TimePoint], statements: List[Statement]):
        unique_timepoints = set(map(lambda x: x.t, timepoints))
        if len(unique_timepoints) != len(timepoints):
            raise LogicException(
                "Only one definition for single time point can exist")
        return cls(timepoints=SortedDict({timepoint.t: timepoint for timepoint in timepoints}), statements=statements)

    @classmethod
    def from_ui(cls, data: dict) -> Scenario:
        try:
            out = cls.from_timepoints(timepoints=TimePoint.from_ui(
                data), statements=Statement.from_ui(data))
        except KeyError:
            raise ParsingException('Failed to parse scenario.')
        return out

    def exist_timepoint(self, t: int) -> bool:
        return t in self.timepoints

    def is_realisable(self) -> bool:
        return True

    def get_first_obs(self, states: List[State]) -> List[Obs]:
        k = next(iter(self.timepoints.keys()), None)
        if k is None:
            raise LogicException('ACS or OBS must be provided')

        all_states: List[Obs] = _get_all_possibilities(list(map(lambda _state: _state.name, states)))
        if not self.timepoints[k].is_obs():
            return all_states
        states = []
        possible_obs = self.timepoints[k].obs.get_all_possibilities()
        
        states = list(
            filter(
                lambda obs: any(
                    list(
                        map(lambda _other: _other.is_superset(obs), 
                            possible_obs))),
                all_states)
        )
        return states

    def get_first_t(self):
        k = next(iter(self.timepoints.values()), None)
        if k is None:
            raise LogicException('ACS or OBS must be provided')
        else:
            return k.t

    def __len__(self):
        return len(self.timepoints)
