from dataclasses import field, dataclass
from typing import Union, List

from . import State
from ..exceptions import BackendExpection


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
            raise BackendExpection("Bad name of the method")
        return Operator.map_methods[name]


@dataclass(slots=True)
class Formula:
    structure: List[Union[str, State]] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str):
        # return cls([])
        pass

    def __bool__(self):
        def _traverse(structure_):
            last_state = None
            operator = None
            for el in structure_:
                if isinstance(el, list):
                    el = _traverse(el)
                if last_state is not None and operator is not None:
                    if operator.__name__ == "not_":
                        return operator(last_state)
                    else:
                        return operator(last_state, el)
                if isinstance(el, (State, bool)):
                    last_state = el
                else:
                    operator = Operator.get(el)

            if operator is not None:
                return operator(last_state)
            return bool(last_state)

        return _traverse(self.structure)
