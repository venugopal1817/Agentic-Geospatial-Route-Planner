from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.planner import build_plan
from app.agents.validation_agent import run_validation_agent

app = FastAPI(
    title="Agentic Geospatial Route Planner",
    description="Multi-agent system for intelligent route planning and village validation"
)


class PlanRequest(BaseModel):
    """Request to plan a route for visiting villages"""
    source: str = Field(default="User", description="Starting location")
    villages: list[str] = Field(..., description="List of village names to visit")


class ValidateRequest(BaseModel):
    """Request to validate matched villages (output from /plan)"""
    source_location: str = Field(default="Unknown", description="Starting location")
    matched_villages: List[dict] = Field(
        ...,
        description="Villages matched by planner, with name, district, coordinates, etc."
    )


@app.get("/")
def read_root() -> dict[str, str]:
    """Health check endpoint"""
    return {"message": "Agentic Geospatial Route Planner API is running"}


@app.post("/plan")
def create_plan(request: PlanRequest) -> dict[str, object]:
    """
    Phase 1: Match villages and resolve ambiguities.
    
    Input: List of village names (may contain typos, duplicates, ambiguities)
    Output: Matched, suggested, and unresolved villages with coordinates
    
    Next: Pass matched output to /validate for multi-source validation
    """
    if not request.villages:
        raise HTTPException(status_code=400, detail="At least one village is required")

    return build_plan(request.villages, source=request.source)


@app.post("/validate")
def validate_villages(request: ValidateRequest) -> dict[str, object]:
    """
    Phase 2: Validate matched villages using LangGraph multi-agent workflow.
    
    Input: Matched villages from /plan endpoint
    Agents involved:
      1. Validator - checks coordinates, sources, data quality
      2. Clarifier - asks user for confirmation if ambiguous
      3. Finalizer - prepares output for route optimization
    
    Output: Validated villages with confidence scores and warnings
    
    Next: Pass validated output to /optimize for route optimization (Week 6)
    """
    if not request.matched_villages:
        raise HTTPException(status_code=400, detail="At least one village required for validation")

    try:
        result = run_validation_agent(
            request.matched_villages,
            source_location=request.source_location
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

