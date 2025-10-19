from pydantic import BaseModel

class AgentPrompt(BaseModel):
    prompt: str