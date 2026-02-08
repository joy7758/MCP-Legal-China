from enum import Enum
from typing import Any, Dict, Optional

class ErrorCode(Enum):
    SUCCESS = 0
    INVALID_PARAMS = -32602
    DB_SYNC_ERROR = 2001
    ELICITATION_REQUIRED = 3001
    INTERNAL_ERROR = -32001
    UNKNOWN_ERROR = 9999

class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "error": self.code.name,
            "message": self.message,
            "details": self.details
        }

class InvalidParamsError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INVALID_PARAMS, message, details)

class DBSyncError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.DB_SYNC_ERROR, message, details)

class ElicitationRequiredError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.ELICITATION_REQUIRED, message, details)

class InternalError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INTERNAL_ERROR, message, details)
