from app.main import app

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/agent")
def run_agent(prompt: str):
    result = run_weather_agent(prompt)
    return {"prompt": prompt, "result": result}
