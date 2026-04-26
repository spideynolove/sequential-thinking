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


def make_error(code: str, message: str, details: dict = None) -> dict:
    err = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return {"error": err}


ID_PREFIXES = {
    "session": "ses_",
    "thought": "thoug_",
    "branch": "bran_",
    "assumption": "assm_",
}


def validate_id_format(id_value: str, id_type: str) -> dict | None:
    prefix = ID_PREFIXES.get(id_type, "")
    if not id_value or not id_value.startswith(prefix):
        return make_error(
            "invalid_id_format",
            f"Invalid {id_type} ID format: '{id_value}'",
            {"field": f"{id_type}_id", "expected_prefix": prefix},
        )
    return None
