from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExecutionCreate(BaseModel):
    workflow_name: str = Field(..., min_length=1, max_length=200)
    input_payload: dict = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    approved: bool
    comment: str = Field(default="", max_length=2000)


class ExecutionEventResponse(BaseModel):
    id: int
    event_type: str
    status: str
    details: str
    actor_id: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExecutionResponse(BaseModel):
    id: int
    workflow_name: str
    status: str
    current_step: str
    input_payload: str
    result_payload: str
    checkpoint: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    events: list[ExecutionEventResponse] = []
    model_config = ConfigDict(from_attributes=True)
