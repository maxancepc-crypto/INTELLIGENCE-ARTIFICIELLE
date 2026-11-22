"""API minimale (déployable sur Render) : POST /run {goal} -> id, GET /runs/{id}."""
import os
import threading
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

load_dotenv()
from core import run  # noqa: E402

app = FastAPI(title="IA autonome gratuite")
RUNS = {}


class Goal(BaseModel):
    goal: str


def _auth(token):
    if token != os.getenv("APP_TOKEN", "changez-moi"):
        raise HTTPException(401, "Jeton invalide")


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/run")
def start(body: Goal, x_token: str = Header(None)):
    _auth(x_token)
    rid = uuid.uuid4().hex[:8]
    RUNS[rid] = {"status": "running", "steps": [], "result": None}

    def job():
        try:
            RUNS[rid]["result"] = run(body.goal, on_step=RUNS[rid]["steps"].append)
            RUNS[rid]["status"] = "done"
        except Exception as e:
            RUNS[rid].update(status="error", result=str(e))

    threading.Thread(target=job, daemon=True).start()
    return {"id": rid}


@app.get("/runs/{rid}")
def get(rid: str, x_token: str = Header(None)):
    _auth(x_token)
    if rid not in RUNS:
        raise HTTPException(404)
    return RUNS[rid]
