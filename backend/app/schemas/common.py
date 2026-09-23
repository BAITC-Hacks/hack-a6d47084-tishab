from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunStatus(str, Enum):
    computed = "computed"
    shadow = "shadow"
    published = "published"
    superseded = "superseded"
    rejected = "rejected"
    failed = "failed"


class IntegrityStatus(str, Enum):
    passed = "pass"
    failed = "failed"
    unknown = "unknown"


class EventStatus(str, Enum):
    success = "success"
    warning = "warning"
    failed = "failed"
    info = "info"


class AgentEvent(StrictModel):
    timestamp: datetime
    type: str
    status: EventStatus
    message: str


class APIError(StrictModel):
    detail: str
