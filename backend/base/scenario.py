from dataclasses import dataclass, field

from sortedcontainers import SortedDict

from . import Statement, TimePoint

from typing import List


@dataclass(slots=True)
class Scenario:
    statements: List[Statement]
    timepoints: SortedDict[int, TimePoint] = field(default_factory=SortedDict)

    @classmethod
    def from_timepoints(cls, timepoints: List[TimePoint], statements: List[Statement]):
        unique_timepoints = set(map(lambda x: x.t, timepoints))
        if len(unique_timepoints) != len(timepoints):
            raise Exception("Only one definition for single time point can exist")
        return cls(timepoints=SortedDict({timepoint.t: timepoint for timepoint in timepoints}), statements=statements)

    def exist_timepoint(self, t: int) -> bool:
        return t in self.timepoints

    def is_realisable(self) -> bool:
        return True

    def __len__(self):
        return len(self.timepoints)
