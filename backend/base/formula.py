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


def evaluate_structure(structure):
    global op
    global st
    global __i
    op = []
    st = []
    __i = 0

    def _evaluate_structure(structure_, depth):
        global __i
        if isinstance(structure_, str):
            structure_ = [structure_]
        for el in structure_:
            __i += 1
            if isinstance(el, list):
                _evaluate_structure(el, depth=depth+1)
            elif el not in list(Operator.map_methods.keys()):
                st.append((el, __i, depth))
            else:
                op.append((el, __i, depth))
        return

    return _evaluate_structure(structure, depth=0)


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
        return sorted(list(filtered))

    def get_all_possibilities(self) -> List[tp.Obs]:
        states = self.extract_states()
        true_states = [obs for obs in _get_all_possibilities(states) if self.bool(obs)]

        return true_states

    def bool(self, obs: tp.Obs):
        global st
        global op

        if not self.structure:
            return True


        def get_max_depth_idx(_list):
            depths = list(map(lambda item: item[2], _list))
            return depths.index(max(depths))

        def get_min_depth(_st, _op):
            depths_op = list(map(lambda item: item[2], _st))
            depths_st = list(map(lambda item: item[2], _op))
            return min([*depths_op, *depths_st])

        def get_by_name_safe_raise(obs: tp.Obs, element: str | bool) -> bool:
            if isinstance(element, bool):
                return element
            el = obs.get_by_name(element)
            if el is None:
                raise exc.LogicException(
                    'State in precondition was not found in OBS.')
            return bool(el)

        evaluate_structure(self.structure)

        min_depth = get_min_depth(st, op)
        if len(op) == 0:
            return get_by_name_safe_raise(obs, self.structure[0])
        while len(op) != 0:
            _operator, _idx, _depth = op.pop(get_max_depth_idx(op))

            idx = get_max_depth_idx(st)
            if _operator == 'not':
                _state, _idx_st, _depth_st = st.pop(idx)
                new_state = Operator.get(_operator)(
                    get_by_name_safe_raise(obs, _state)
                )
            else:
                _state_l, _idx_st, _depth_st = st.pop(idx)
                _state_r, _idx_st_r, _depth_st_r = st.pop(
                    get_max_depth_idx(st))
                new_state = Operator.get(_operator)(
                    get_by_name_safe_raise(obs, _state_l),
                    get_by_name_safe_raise(obs, _state_r)
                )
            new_depth = max(min_depth, _depth_st - 1)
            st.insert(idx, (new_state, idx, new_depth))
        assert len(st) == 1 and len(st[0]) == 3
        return st[0][0]

    # def bool(self, obs: tp.Obs):

    #     if not self.structure:
    #         return True

    #     def get_by_name_safe_raise(obs: tp.Obs, element: str | bool) -> State:
    #         if isinstance(element, bool):
    #             return element
    #         el = obs.get_by_name(element)
    #         if el is None:
    #             raise exc.LogicException('State in precondition was not found in OBS.')
    #         return el

    #     def _traverse(structure_):
    #         last_state = None
    #         operator = None
    #         if isinstance(structure_, str):
    #             structure_ = [structure_]
    #         for el in structure_:
    #             if isinstance(el, list):
    #                 el = _traverse(el)
    #             if last_state is not None and operator is not None:
    #                 if operator.__name__ == "not_":
    #                     return operator(last_state)
    #                 else:
    #                     _el = get_by_name_safe_raise(obs, el)
    #                     return operator(last_state, _el)
    #             if el not in list(Operator.map_methods.keys()):
    #                 last_state = get_by_name_safe_raise(obs, el)
    #             else:
    #                 operator = Operator.get(el)

    #         if operator is not None:
    #             return operator(last_state)
    #         return bool(last_state)

    #     return _traverse(self.structure)
