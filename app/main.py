from fastapi import FastAPI
from app.routers.agent import router as agent_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Include routers
app.include_router(agent_router)