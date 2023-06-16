from __future__ import annotations

import itertools

from . import State
from . import timepoint as tp

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


def _get_all_possibilities(states: List[str]) -> List[tp.Obs]:
    return [
        tp.Obs([
            State(state_name, holds=permutation[i]) for i, state_name in enumerate(states)
        ]) for permutation in itertools.product([True, False], repeat=len(states))]


@dataclass(slots=True)
class Formula:
    structure: List[Union[str, str]] = field(default_factory=list)

    @classmethod
    def from_ui(cls, data: str) -> Formula:
        try:
            if not data:
                out = None
            else:
                out = data if isinstance(data, list) else [data]
        except KeyError:
            raise exc.ParsingException('Failed to parse precondition.')
        return cls(structure=out)

    def extract_states(self) -> List[str]:
        keywords = set(el for el in list(Operator.map_methods.keys()))
        filtered = set(filter(lambda x: x not in keywords, flatten(self.structure)))
        return sorted(list(filtered))

    def get_all_possibilities(self) -> List[tp.Obs]:
        if self.structure == []:
            return []
        states = self.extract_states()
        true_states = [obs for obs in _get_all_possibilities(states) if self.bool(obs)]

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
            last_states = []
            operator = None
            if isinstance(structure_, str):
                structure_ = [structure_]
            for el in structure_:
                if isinstance(el, list):
                    el = _traverse(el)

                if el not in list(Operator.map_methods.keys()):
                    last_states.append(get_by_name_safe_raise(obs, el))
                else:
                    operator = Operator.get(el)

                if len(last_states) > 0 and operator is not None:
                    if operator.__name__ == "not_":
                        el = last_states.pop()
                        last_states.append(operator(el))
                        operator = None
                    elif len(last_states) >= 2:
                        el = last_states.pop()
                        previous_el = last_states.pop()
                        last_states.append(operator(previous_el, el))
                        operator = None

            if operator is not None:
                el = last_states.pop()
                return operator(el)

            return bool(last_states[0])

        return _traverse(self.structure)
