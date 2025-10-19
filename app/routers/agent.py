from fastapi import APIRouter
from app.schemas.agent import AgentPrompt
from app.agent.agent_main import run_incident_agent

router = APIRouter()

@router.post("/agent/incident")
def run_incident(req: AgentPrompt):
    result = run_incident_agent(req.prompt)
    return {"prompt": req.prompt, "result": result}