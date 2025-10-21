from pydantic import BaseModel, Field

class AgentPrompt(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt; must be non-empty.")