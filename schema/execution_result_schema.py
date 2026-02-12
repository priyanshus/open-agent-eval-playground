from typing import Any, List

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    success: bool = Field(..., description="Whether all tools completed without failure")
    outputs: List[Any] = Field(
        default_factory=list,
        description="Ordered results from each executed tool",
    )
    error: str | None = Field(
        default=None,
        description="Error message when success is False",
    )
