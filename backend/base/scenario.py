from dataclasses import dataclass, field

from sortedcontainers import SortedDict

from . import Statement, TimePoint, Obs
from . import LogicExpection

from typing import List, Optional


@dataclass(slots=True)
class Scenario:
    statements: List[Statement]
    timepoints: SortedDict[int, TimePoint] = field(default_factory=SortedDict)

    @classmethod
    def from_timepoints(cls, timepoints: List[TimePoint], statements: List[Statement]):
        unique_timepoints = set(map(lambda x: x.t, timepoints))
        if len(unique_timepoints) != len(timepoints):
            raise LogicExpection("Only one definition for single time point can exist")
        return cls(timepoints=SortedDict({timepoint.t: timepoint for timepoint in timepoints}), statements=statements)

    def exist_timepoint(self, t: int) -> bool:
        return t in self.timepoints

    def is_realisable(self) -> bool:
        return True

    def get_first_obs(self, quiet=False) -> Optional[Obs]:
        try:
            k = list(self.timepoints.keys())[0]
            if not self.timepoints[k].is_obs():
                raise LogicExpection()
            return self.timepoints[k].obs
        except (IndexError, LogicExpection) as e:
            if not quiet:
                raise LogicExpection('OBS must be defined before any action can be performed (ACS).')
            else:
                return None

    def __len__(self):
        return len(self.timepoints)
