
from typing import List
from pydantic import BaseModel, Field


class ExecutionPlanSchema(BaseModel):
    route: str = Field(..., description="Name of the execution flow")
    requires_tools: bool = Field(
        ..., description="Whether external tools need to be executed"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Ordered list of tool names to execute"
    )