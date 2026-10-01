from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    document_type: str = "Document"
    content: str = ""


class DocumentResponse(DocumentCreate):
    id: int
    tenant_id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    workflow_type: str = "general"


class WorkflowResponse(WorkflowCreate):
    id: int
    tenant_id: int
    created_by_id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
