from pydantic import Field

from .common import AgentEvent, StrictModel


class AgentResult(StrictModel):
    status: str
    summary: str | None = None
    decision: str | None = None
    warnings: list[str] = Field(default_factory=list)
    operator_message: str | None = None
    fallback: str | None = None
    activity: list[AgentEvent] = Field(default_factory=list)
    is_mock: bool = False
    llm_used: bool = False
    briefing_reason: str | None = None
