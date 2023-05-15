from dataclasses import dataclass


@dataclass(slots=True)
class State:
    name: str
    holds: bool = True

    def __bool__(self) -> bool:
        return self.holds
