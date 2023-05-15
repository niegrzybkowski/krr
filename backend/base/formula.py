from dataclasses import field, dataclass
from typing import Union, List

from . import State


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
