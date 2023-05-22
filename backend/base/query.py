from __future__ import annotations

import copy
from dataclasses import dataclass, astuple
from typing import List

from . import LogicException, ParsingException
from . import State, Scenario, Agent, Statement, Obs, Action, TimePoint, Formula


@dataclass(slots=True)
class QuasiModel:
    path: List[TimePoint]

    def get_last_timepoint(self):
        return self.path[-1]

    def is_performing_action_in_t(self, action: Action, time: int) -> bool:
        for timepoint in self.path:
            if timepoint.t - 1 == time and timepoint.acs[0] == action:
                return True
        return False

    def is_agent_active(self, agent: Agent) -> bool:
        prev_timepoint = None
        for timepoint in self.path:
            if timepoint.acs is not None and \
                    timepoint.acs[1] == agent and \
                    set(astuple(state) for state in prev_timepoint.obs.states) != \
                    set(astuple(state) for state in timepoint.obs.states):
                return True
            prev_timepoint = timepoint
        return False

    def condition_holds(self, possibilities: List[Obs], time: int) -> bool:
        fluents = None
        for timepoint in self.path:
            if timepoint.t <= time:
                fluents = Obs(
                    states=[
                        timepoint.obs.get_state_by_name(state.name)
                        for state in possibilities[0].states
                    ])

        return False if fluents is None else any(fluents.is_superset(possibility) for possibility in possibilities)


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
    def from_ui(cls, scenario, termination, data: dict) -> List[ActionQuery | FormulaQuery | AgentQuery]:
        try:
            _types = {
                "action": ActionQuery,
                "fluent": FormulaQuery,
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

            new_models = []
            for model in cur_models:
                tp = model.get_last_timepoint()
                _res: List[Obs] = action.run(tp.obs, statements)
                if _res:
                    for _obs in _res:
                        # create
                        new_tp = TimePoint(
                            t=t + 1,
                            obs=_obs,
                            acs=(action, agent)
                        )
                        new_path = copy.deepcopy(model.path)
                        new_path.append(new_tp)
                        new_models.append(QuasiModel(new_path))
                else:
                    new_models.append(model)

            cur_models = new_models
        return cur_models


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
class FormulaQuery(Query):
    formula: Formula = None
    time: int = None
    mode: str = None  # 'necessary', 'possibly'
    possibilities: List[Obs] = None

    def __post_init__(self):
        self.mode = self.mode.lower()
        self.possibilities = self.formula.get_all_possibilities()

        if self.mode not in ['necessary', 'possibly']:
            raise LogicException(
                "Fluent Query can be executed only in 'necessary' or 'possibly' mode.")

    @classmethod
    def from_ui(cls, scenario, termination, data: dict) -> FormulaQuery:
        try:
            out = cls(scenario=scenario, termination=termination,
                      formula=State(name=data['condition']),
                      time=data['time'],
                      mode=data['kind']
                      )
        except (KeyError, TypeError):
            raise ParsingException('Failed to parse fluent query.')
        return out

    def run(self) -> str:
        models = super(FormulaQuery, self).run()
        if len(models) != 0:
            condition_models = [model.condition_holds(self.possibilities, self.time) for model in models]
            if self.mode == 'necessary':
                if all(condition_models):  # TODO: add formula
                    return f"Formula always holds at t={self.time}"
                return f"Formula doesn't always hold at t={self.time}"
            if any(condition_models):
                return f"Formula sometimes holds at t={self.time}"
            return f"Formula never holds at t={self.time}"


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
