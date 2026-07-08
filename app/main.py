from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.planner import build_plan

app = FastAPI(title="Agentic Geospatial Route Planner")


class PlanRequest(BaseModel):
    source: str = "User"
    villages: list[str]


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Agentic Geospatial Route Planner API is running"}


@app.post("/plan")
def create_plan(request: PlanRequest) -> dict[str, object]:
    if not request.villages:
        raise HTTPException(status_code=400, detail="At least one village is required")

    return build_plan(request.villages, source=request.source)
