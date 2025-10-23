# Datapizza AI Demo Server

FastAPI application integrating AI tools and a DAG pipeline.

## Local Run
- `uv pip install --system -r requirements.txt` (use `uv export --frozen -o requirements.txt` if needed)
- `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Docker
- Build: `docker build -t datapizza-ai-demo:latest .`
- Run: `docker run --rm -p 8000:8000 -e OPENAI_API_KEY=your_key datapizza-ai-demo:latest`