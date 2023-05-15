from dataclasses import dataclass


@dataclass(slots=True)
class Agent:
    """ Class for Agent"""
    name: str
    active: bool = False

    def __bool__(self):
        return self.active
