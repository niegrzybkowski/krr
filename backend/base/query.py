from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List, Tuple

from . import LogicException, ParsingException
from . import State, Scenario, Agent, Statement, Obs, Action, TimePoint


@dataclass(slots=True)
class QuasiModel:
    path: List[TimePoint]

    def get_last_timepoint(self):
        return self.path[-1]


@dataclass(slots=True)
class Query:
    scenario: Scenario
    termination: int
    states: List[State] = None

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> List[ActionQuery | FluentQuery | AgentQuery]:
        try:
            _types = {
                "action": ActionQuery,
                "fluent": FluentQuery,
                "agent": AgentQuery,
            }
            out = [_types[item['query_type']].from_ui(scenario, termination, item['concrete_query']) for item in
                   data['QUERY']]
        except KeyError:
            raise ParsingException('Failed to parse query.')
        return out

    def run(self) -> List[QuasiModel]:

        cur_obs: List[Obs] = self.scenario.get_first_obs(states=self.states)
        first_t: int = self.scenario.get_first_t()
        cur_models: List[QuasiModel] = [
            QuasiModel(
                path=[
                    TimePoint(
                        t=first_t,
                        obs=obs
                    ) for obs in cur_obs])
        ]

        for t, timepoint in self.scenario.timepoints.items():
            if not timepoint.is_acs():
                continue
            if t > self.termination:
                break

            if timepoint.is_obs():
                cur_models = list(
                    filter(lambda model: model.get_last_timepoint().obs.is_superset(timepoint.obs),
                           cur_models)
                )

            action, agent = timepoint.acs

            statements: List[Statement] = get_statements(action, agent, self.scenario.statements)

            # cur_obs = [action.run(agent, obs, statements) for obs in cur_obs]
            new_models = []
            for model in cur_models:
                tp = model.get_last_timepoint()
                _res: List[Obs] = action.run(agent, tp.obs, statements)
                if _res:
                    for _obs in _res:
                        # create
                        new_tp = TimePoint(
                            t=tp.t + 1,
                            obs=_obs,
                            acs=(action, agent)
                        )
                        new_path = copy.deepcopy(model.path)
                        new_path.append(new_tp)
                        new_models.append(QuasiModel(new_path))
                else:
                    new_models.append(model)

            # flatten = flatten_list(cur_obs)
            # cur_obs = eliminate_duplicates(flatten)

            cur_models = new_models
        return cur_models

    def is_valid(self) -> None:
        # raise LogicException("...")
        # obs must be defined for smallest timepoint in scenario
        raise NotImplementedError()


@dataclass(slots=True)
class ActionQuery(Query):
    action: Action = None

    # agent: Agent # TODO: uwzględnienie agenta i punktu w czasie
    # timepoint: int

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> ActionQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      action=Action(name=data['action']),
                      #   agent=Agent(name=data['agent']),
                      #   timepoint=data['time']
                      )
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse action query.')
        return out

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
                is_performed = bool(action)
            if is_performed:
                break

        if is_performed:
            return f"Action {self.action.name} is performed in this Scenario"

        return f"Action {self.action.name} is performed in this Scenario"


@dataclass(slots=True)
class FluentQuery(Query):
    fluent: State = None
    timepoint: int = None
    mode: str = None  # 'necessary', 'possibly'

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> ActionQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      fluent=State(name=data['condition']),
                      timepoint=data['time'],
                      mode=data['kind']
                      )
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse fluent query.')
        return out

    def __post_init__(self):
        mode = self.mode.lower()

        if mode not in ['necessary', 'possibly']:
            raise LogicException(
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
                    raise LogicException(f'State {_state.name} was not found in OBS')
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
    agent: Agent = None

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> ActionQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      agent=Agent(name=data['agent'])
                      )
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse agent query.')
        return out

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
