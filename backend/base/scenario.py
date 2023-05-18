from __future__ import annotations
# import os,sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from dataclasses import dataclass, field

from sortedcontainers import SortedDict

from .  import Statement
from .  import TimePoint, Obs
from exception import LogicException, ParsingException

from typing import List, Optional


@dataclass(slots=True)
class Scenario:
    statements: List[Statement]
    timepoints: SortedDict[int, TimePoint] = field(default_factory=SortedDict)

    @classmethod
    def from_timepoints(cls, timepoints: List[TimePoint], statements: List[Statement]):
        unique_timepoints = set(map(lambda x: x.t, timepoints))
        if len(unique_timepoints) != len(timepoints):
            raise LogicException("Only one definition for single time point can exist")
        return cls(timepoints=SortedDict({timepoint.t: timepoint for timepoint in timepoints}), statements=statements)

    @classmethod
    def from_ui(cls, data: dict) -> Scenario:
        try:
            out = cls.from_timepoints(timepoints=TimePoint.from_ui(data), statements=Statement.from_ui(data))
        except KeyError:
            raise ParsingException('Failed to parse scenario.')
        return out

    def exist_timepoint(self, t: int) -> bool:
        return t in self.timepoints

    def is_realisable(self) -> bool:
        return True

    def get_first_obs(self, quiet=False) -> Optional[Obs]:
        try:
            k = list(self.timepoints.keys())[0]
            if not self.timepoints[k].is_obs():
                raise LogicException()
            return self.timepoints[k].obs
        except (IndexError, LogicException) as e:
            if not quiet:
                raise LogicException('OBS must be defined before any action can be performed (ACS).')
            else:
                return None

    def __len__(self):
        return len(self.timepoints)
