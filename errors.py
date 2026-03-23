class SequentialThinkingError(Exception):
    pass


class SessionError(SequentialThinkingError):
    pass


class NoActiveSessionError(SessionError):
    pass


class SessionNotFoundError(SessionError):
    pass


class ValidationError(SequentialThinkingError):
    pass


class StorageError(SequentialThinkingError):
    pass


class MemoryError(SequentialThinkingError):
    pass


class BranchError(SequentialThinkingError):
    pass


class PackageExplorationError(SequentialThinkingError):
    pass


class ExportError(SequentialThinkingError):
    pass
