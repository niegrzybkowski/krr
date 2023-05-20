from __future__ import annotations

import itertools

from . import State
from . import timepoint as tp  # Obs

from . import exception as exc
from dataclasses import field, dataclass
from typing import Union, List, Iterable


class Operator:
    @staticmethod
    def not_(state: Union[State, bool]) -> bool:
        return not bool(state)

    @staticmethod
    def and_(state1: Union[State, bool], state2: Union[State, bool]) -> bool:
        return bool(state1) and bool(state2)

    @staticmethod
    def or_(state1: Union[State, bool], state2: Union[State, bool]) -> bool:
        return bool(state1) or bool(state2)

    @staticmethod
    def implies_(state1: Union[State, bool], state2: Union[State, bool]) -> bool:
        return not bool(state1) or bool(state2)

    @staticmethod
    def if_and_only_if_(state1: Union[State, bool], state2: Union[State, bool]) -> bool:
        return bool(state1) == bool(state2)

    map_methods = {
        "not": not_,
        "and": and_,
        "or": or_,
        "implies": implies_,
        "if and only if": if_and_only_if_
    }

    @staticmethod
    def get(name: str):
        if name not in Operator.map_methods:
            raise exc.BackendException("Bad name of the method")
        return Operator.map_methods[name]


def flatten(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


@dataclass(slots=True)
class Formula:
    structure: List[Union[str, str]] = field(default_factory=list)

    @classmethod
    def from_ui(cls, data: dict) -> Formula:
        try:
            out = data['condition']
        except KeyError:
            raise exc.ParsingException('Failed to parse precondition.')
        return cls(structure=out)

    def extract_states(self) -> List[str]:
        keywords = set(el for el in list(Operator.map_methods.keys()))
        filtered = set(filter(lambda x: x not in keywords, flatten(self.structure)))
        return list(filtered)

    def get_all_posibilites(self) -> List[tp.Obs]:
        states = self.extract_states()
        true_states = []
        for permutation in itertools.product([True, False], repeat=len(states)):
            actual_obs_state = [State(state_name, holds=permutation[i])
                                for i, state_name in enumerate(states)]
            obs = tp.Obs(actual_obs_state)
            if self.bool(obs):
                true_states.append(obs)
        return true_states

    def bool(self, obs: tp.Obs):

        if not self.structure:
            return True

        def get_by_name_safe_raise(obs: tp.Obs, element: str | bool) -> State:
            if isinstance(element, bool):
                return element
            el = obs.get_by_name(element)
            if el is None:
                raise exc.LogicException('State in precondition was not found in OBS.')
            return el

        def _traverse(structure_):
            last_state = None
            operator = None
            if isinstance(structure_, str):
                structure_ = [structure_]
            for el in structure_:
                if isinstance(el, list):
                    el = _traverse(el)
                if last_state is not None and operator is not None:
                    if operator.__name__ == "not_":
                        return operator(last_state)
                    else:
                        _el = get_by_name_safe_raise(obs, el)
                        return operator(last_state, _el)
                if el not in list(Operator.map_methods.keys()):
                    last_state = get_by_name_safe_raise(obs, el)
                else:
                    operator = Operator.get(el)

            if operator is not None:
                return operator(last_state)
            return bool(last_state)

        return _traverse(self.structure)
