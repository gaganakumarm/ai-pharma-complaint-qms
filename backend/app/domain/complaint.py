from enum import StrEnum


class ProductType(StrEnum):
    API = "API"
    FDF = "FDF"
    UNKNOWN = "UNKNOWN"


class ComplaintSeverity(StrEnum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class ComplaintStatus(StrEnum):
    PENDING_TRIAGE = "PENDING_TRIAGE"
    READY_TO_COMMIT = "READY_TO_COMMIT"
    COMMITTED = "COMMITTED"


class SourceType(StrEnum):
    MANUAL = "MANUAL"
    TEXT = "TEXT"
    PDF = "PDF"
