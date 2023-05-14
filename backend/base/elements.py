from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

from sortedcontainers import SortedDict


@dataclass(slots=True)
class Agent:
    """ Class for Agent"""
    name: str
    active: bool = False

    def __bool__(self):
        return self.active


@dataclass(slots=True)
class State:
    name: str
    holds: bool = True

    def __bool__(self) -> bool:
        return self.holds


class Operator:
    name: str

    @staticmethod
    def get(self, name: str, *args, **kwargs):
        pass

    @staticmethod
    def not_(state: Union[State, bool]):
        return lambda: not state

    @staticmethod
    def and_(state1: State, state2: State):
        return lambda: state1 and state2

    @staticmethod
    def or_(state1: State, state2: State):
        return lambda: state1 or state2

    @staticmethod
    def implies_(state1: State, state2: State):
        return lambda: not state1 or state2

    @staticmethod
    def if_and_only_if_(state1: State, state2: State):
        return lambda: bool(state1) == bool(state2)


@dataclass(slots=True)
class Formula:
    structure: List[Union[State, Operator]] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str):
        # return cls([])
        pass

    def __bool__(self):
        # TODO: lista list
        return True


@dataclass(slots=True)
class Statement(ABC):
    action: "Action"
    agent: Agent
    precondition: Formula

    def __bool__(self):
        return bool(self.precondition)


@dataclass(slots=True)
class EffectStatement(Statement):
    postcondition: List[State]


@dataclass(slots=True)
class ReleaseStatement(Statement):
    postcondition: List[State]


@dataclass(slots=True)
class Action:
    name: str

    def run(self, agent: Agent, obs: List[State], statements: List[Statement]) -> List[List[State]]:
        """run action by agent if """
        postconditions = [[]]
        for statement in filter(lambda statement: isinstance(statement, EffectStatement), statements):
            if statement.precondition:
                agent.active = True
                postconditions[0].extend(statement.postcondition)

        for statement in filter(lambda statement: isinstance(statement, ReleaseStatement), statements):
            if statement.precondition:
                agent.active = True

                psc = []
                psc2= []
                for postcondition in postconditions:
                    temp = copy(postcondition)
                    temp.extend(statement.postcondition)
                    psc2.append(temp)
                    psc.append(copy(postcondition))

                postconditions.extend(psc)
                postconditions.extend(psc2)

        new_obs = []
        for postcondition in postconditions:
            temp = update(copy(obs), postcondition)
            new_obs.append(temp)

        return new_obs


def update(original_list: List[State], update_list: List[State]):
    """ validation state unique by name and holds """

    update_tuples_nh = set(map(lambda state: (state.name, state.holds), update_list))
    update_tuples_n = set(map(lambda state: (state.name,), update_list))
    if len(update_tuples_nh) != len(update_tuples_n):
        raise Exception('Scenario is not realizable - statement contains disjoint statements')

    _update = [State(name=name, holds=holds) for name, holds in update_tuples_nh]

    for update_element in _update:
        el = next(filter(lambda state: state.name == update_element.name, original_list))

        el.holds = update_element.holds

    return original_list


@dataclass(slots=True)
class Query(ABC):
    scenario: 'Scenario'
    termination: int

    @abstractmethod
    def run(self) -> str:
        pass

    def is_valid(self) -> None:
        # raise Exception("...")
        # obs must be defined for smallest timepoint in scenario
        pass


@dataclass(slots=True)
class ActionQuery(Query):

    @abstractmethod
    def run(self) -> str:
        pass

    def is_valid(self):
        super().is_valid()


@dataclass(slots=True)
class FluentQuery(Query):
    fluent: State
    type: str  # always/ever || necessary/possible

    @abstractmethod
    def run(self) -> str:
        pass


def get_statements(action, agent, statements) -> List[Statement]:
    filtered_statements = list(filter(lambda x: x.action == action and x.agent == agent, statements))
    if not filtered_statements:
        raise Exception("Statement not provided")
    return filtered_statements


@dataclass(slots=True)
class AgentQuery(Query):
    agent: Agent

    def run(self) -> str:
        # super().is_valid()

        is_active = False
        cur_obs = [self.scenario.timepoints[list(self.scenario.timepoints.keys())[0]].obs]

        for t, timepoint in self.scenario.timepoints.items():

            # running_timepoint = TimePoint(t=t, acs=timepoint.acs, obs=timepoint.obs)
            # running_scenario.timepoints[t]

            if not timepoint.is_acs():
                continue
            if t > self.termination:
                break

            action, agent = timepoint.acs

            statements: List[Statement] = get_statements(action, agent, self.scenario.statements)

            cur_obs = [action.run(agent, obs, statements) for obs in cur_obs]

            if agent.name == self.agent.name:
                is_active = bool(agent)

            if is_active:
                break

        if is_active:
            return f"Agent {self.agent.name} is active in this Scenario"

        return f"Agent {self.agent.name} is not active in this Scenario"


@dataclass(slots=True)
class TimePoint:
    t: int
    acs: Optional[Tuple[Action, Agent]] = None
    obs: Optional[List[State]] = None

    def is_acs(self):
        return self.acs is not None

    def is_obs(self):
        return self.obs is not None


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
