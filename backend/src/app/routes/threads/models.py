from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    thread_id: str | None = Field(default=None, description="Optional custom thread id")
    title: str | None = Field(default=None, description="Optional thread title")
    status: Literal["active", "archived"] = Field(default="active")


class UpdateThreadRequest(BaseModel):
    title: str | None = Field(default=None, description="Thread title")
    status: Literal["active", "archived"] | None = Field(default=None)
