class BackendException(Exception):
    pass


class ParsingException(BackendException):
    pass


class LogicException(BackendException):
    pass
