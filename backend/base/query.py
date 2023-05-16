from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from . import State, Scenario, Agent, Statement, Obs, Action


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
    action: Action

    def run(self) -> str:
        # super().is_valid()
        is_performed = False
        cur_obs = [self.scenario.get_first_obs()]

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

            if action == self.action:
                is_performed = bool(self.action)
            if is_performed:
                break

        if is_performed:
            return f"Action {self.action.name} is performed in this Scenario"

        return f"Action {self.action.name} is performed in this Scenario"


@dataclass(slots=True)
class FluentQuery(Query):
    fluent: State  # TODO: confirm whether fluent can be formula - PM it don't think so
    timepoint: int
    mode: str  # 'necessary', 'possibly'

    def __post_init__(self):
        mode = self.mode.lower()

        if mode not in ['necessary', 'possibly']:
            raise ValueError(
                "Fluent Query can be executed only in 'necessary' or 'possibly' mode.")

    def run(self) -> str:
        # super().is_valid()

        cur_obs = [self.scenario.get_first_obs()]
        if self.timepoint > self.termination:
            return "It is impossible to determine since considered " \
                   f"timepoint is greater than termination ({self.timepoint} > {self.termination})"

        for t, timepoint in self.scenario.timepoints.items():
            if not timepoint.is_acs():
                continue
            if t >= self.timepoint:
                break

            action, agent = timepoint.acs

            statements: List[Statement] = get_statements(
                action, agent, self.scenario.statements)

            cur_obs = [action.run(agent, obs, statements) for obs in cur_obs]
            flatten = flatten_list(cur_obs)
            cur_obs = eliminate_duplicates(flatten)

        def __getStatesByName(_list: List[Obs], _state: State) -> List[State]:
            res = []
            for el in _list:
                __state: State = next(
                    filter(lambda item: item.name == _state.name, el), None)
                if __state is None:
                    raise Exception(f'State {_state.name} was not found in OBS')
                res.append(__state)
            return res

        cur_states = __getStatesByName(cur_obs, self.fluent)

        if self.mode == 'necessary':
            if all(cur_states):
                return f"Fluent {self.fluent.name} always holds at t={self.timepoint}"
            return f"Fluent {self.fluent.name} doesn't always hold at t={self.timepoint}"
        # 'possibly':
        if any(cur_states):
            return f"Fluent {self.fluent.name} sometimes holds at t={self.timepoint}"
        return f"Fluent {self.fluent.name} never holds at t={self.timepoint}"


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
        cur_obs = [self.scenario.get_first_obs()]

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
