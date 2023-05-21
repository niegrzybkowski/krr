from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List

from . import LogicException, ParsingException
from . import State, Scenario, Agent, Statement, Obs, Action, TimePoint


@dataclass(slots=True)
class QuasiModel:
    path: List[TimePoint]

    def get_last_timepoint(self):
        return self.path[-1]

    def is_performing_action_in_t(self, action: Action, time: int) -> bool:
        for timepoint in self.path:
            if timepoint.t == time and timepoint.acs[0] == action:
                return True
        return False

    def is_agent_active(self, agent: Agent) -> bool:
        for timepoint in self.path:
            if timepoint.acs is not None and timepoint.acs[1] == agent:
                return True
        return False

    def extract_fluent(self, state: State, time: int) -> List[State]:
        for timepoint in self.path:
            if timepoint.t <= time:
                fluent = timepoint.obs.get_state_by_name(state.name)
        return fluent


def get_statements(action, agent, statements) -> List[Statement]:
    filtered_statements = list(
        filter(lambda x: x.action == action and x.agent == agent, statements))
    return filtered_statements


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
                path=[TimePoint(
                    t=first_t,
                    obs=obs
                )]) for obs in cur_obs
        ]

        for t, timepoint in self.scenario.timepoints.items():
            if t > self.termination:
                break

            if timepoint.is_obs():
                possible_obs: List[Obs] = timepoint.obs.get_all_possibilities()
                cur_models = list(
                    filter(
                        lambda model: any(
                            list(
                                map(lambda _other: _other.is_superset(model.get_last_timepoint().obs), possible_obs))),
                        cur_models)
                )
                if len(cur_models) == 0:
                    raise LogicException('This scenario is not realizable')

            if not timepoint.is_acs():
                continue

            action, agent = timepoint.acs

            statements: List[Statement] = get_statements(
                action, agent, self.scenario.statements)

            # cur_obs = [action.run(agent, obs, statements) for obs in cur_obs]
            new_models = []
            for model in cur_models:
                tp = model.get_last_timepoint()
                _res: List[Obs] = action.run(tp.obs, statements)
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
    time: int = None

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> ActionQuery:
        try:
            out = cls(
                scenario=scenario, termination=termination,
                action=Action(name=data['action']),
                time=data['time']
            )
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse action query.')
        return out

    def run(self) -> str:
        models = super(ActionQuery, self).run()
        is_performed = False
        if len(models) != 0:
            for model in models:
                if model.is_performing_action_in_t(self.action, self.time):
                    is_performed = True

        if is_performed:
            return f"Action {self.action.name} is performed in moment {self.time} in this Scenario"

        return f"Action {self.action.name} is not performed in moment {self.time} in this Scenario"


@dataclass(slots=True)
class FluentQuery(Query):
    fluent: State = None
    time: int = None

    mode: str = None  # 'necessary', 'possibly'

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> FluentQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      fluent=State(name=data['condition']),
                      time=data['time'],
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
        models = super(FluentQuery, self).run()
        if len(models) != 0:
            fluents = [model.extract_fluent(self.fluent, self.time) for model in models]
            if self.mode == 'necessary':
                if all(fluents):
                    return f"Fluent {self.fluent.name} always holds at t={self.time}"
                return f"Fluent {self.fluent.name} doesn't always hold at t={self.time}"
            if any(fluents):
                return f"Fluent {self.fluent.name} sometimes holds at t={self.time}"
            return f"Fluent {self.fluent.name} never holds at t={self.time}"


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
    def from_ui(cls, scenario, termination, data: dict) -> AgentQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      agent=Agent(name=data['agent']))
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse agent query.')
        return out

    def run(self) -> str:
        models = super(AgentQuery, self).run()
        is_active = True
        if len(models) != 0:
            for model in models:
                if not model.is_agent_active(self.agent):
                    is_active = False
                    break

        if is_active:
            return f"Agent {self.agent.name} is active in this Scenario"

        return f"Agent {self.agent.name} is not active in this Scenario"
