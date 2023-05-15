from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from . import State, Scenario, Agent, Statement, Obs


@dataclass(slots=True)
class Query(ABC):
    scenario: Scenario
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
    return filtered_statements


def flatten_list(_list: List[List[Obs]]) -> List[Obs]:
    res = []
    for el in _list:
        res.extend(el)
    return res


def eliminate_duplicates(_list: List[Obs]) -> List[Obs]:
    res = []
    for el in _list:
        if el not in res:
            res.append(el)
    return res


@dataclass(slots=True)
class AgentQuery(Query):
    agent: Agent

    def run(self) -> str:
        # super().is_valid()

        is_active = False
        cur_obs = [self.scenario.timepoints[list(self.scenario.timepoints.keys())[0]].obs]

        for t, timepoint in self.scenario.timepoints.items():
            if not timepoint.is_acs():
                continue
            if t > self.termination:
                break

            action, agent = timepoint.acs

            statements: List[Statement] = get_statements(action, agent, self.scenario.statements)

            cur_obs = [action.run(agent, obs, statements) for obs in cur_obs]
            flatten = flatten_list(cur_obs)
            cur_obs = eliminate_duplicates(flatten)

            if agent.name == self.agent.name:
                is_active = bool(agent)

            if is_active:
                break

        if is_active:
            return f"Agent {self.agent.name} is active in this Scenario"

        return f"Agent {self.agent.name} is not active in this Scenario"
