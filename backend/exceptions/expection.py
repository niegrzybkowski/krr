class BackendExpection(Exception):
    pass


class ParsingException(BackendExpection):
    pass


class LogicExpection(BackendExpection):
    pass
