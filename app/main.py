"""Server scaffold. Provided, do not edit (your work goes in app/agent.py)."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import agent
from app import solution
from app import helpers

app = FastAPI(title="Recipe note-taker")
STATIC = Path(__file__).parent / "static"

class Query(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    reply: str

class AgentOut(BaseModel):
    reply: str
    notes: list[str]

def _run(body: Query) -> str:
    try:
        return agent.run_agent(body.message)
        #return solution.run_agent(body.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")

@app.post("/chat", response_model=ChatOut)
def chat(body: Query):
    """Used by the frontend."""
    return ChatOut(reply=_run(body))

@app.post("/agent/query", response_model=AgentOut)
def agent_query(body: Query):
    """Used by scripts/grade.py: returns the reply and the current notes."""
    reply = _run(body)
    return AgentOut(reply=reply, notes=helpers.get_notes())

@app.get("/notes")
def get_notes():
    return {"notes": helpers.get_notes()}

@app.get("/agent/reset")
def reset():
    helpers._NOTES = []
    helpers._INGREDIENTS = []