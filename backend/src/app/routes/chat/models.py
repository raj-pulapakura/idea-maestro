from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="User message text")
    client_message_id: Optional[str] = Field(
        default=None,
        description="Optional client-side ID for optimistic UI bookkeeping",
    )


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject", "request_changes"] = Field(
        description="approve, reject, or request_changes"
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional reviewer comment for the decision",
    )
    interrupt_id: Optional[str] = Field(
        default=None,
        description="Optional LangGraph interrupt id for targeted resume",
    )
