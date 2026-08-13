from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.planner import build_plan
from app.services.optimizer import optimize_route
from app.services.retrieval import VillageRetrievalService
from app.services.intent_parser import IntentParser
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


class OptimizeRequest(BaseModel):
    """Request to optimize a route from validated villages."""
    source_location: str = Field(default="Unknown", description="Starting location")
    villages: List[dict] = Field(
        ...,
        description="Validated village list with name, latitude, longitude, district, subdistric"
    )


class WorkflowRequest(BaseModel):
    """Single end-to-end request for planning, validation, and optimization."""
    source_location: str = Field(default="Unknown", description="Starting location")
    villages: List[str] = Field(..., description="Village names to process")
    use_llm_summary: bool = Field(default=False, description="Whether to enable an LLM summary hook")


class NaturalLanguageRequest(BaseModel):
    """User request in natural language to be parsed and resolved."""
    request_text: str = Field(..., description="A natural-language route request")


class ClarificationRequest(BaseModel):
    """User clarification response for a selected village candidate."""
    session_id: str = Field(..., description="Planning session identifier")
    selected_option_id: str = Field(..., description="Selected candidate location id")


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


@app.post("/optimize")
def optimize_villages(request: OptimizeRequest) -> dict[str, object]:
    """
    Phase 3: Route optimization for validated villages.

    Input: Validated village records with latitude/longitude
    Output: Route order, total distance, and estimated travel time
    """
    if not request.villages:
        raise HTTPException(status_code=400, detail="At least one village is required for optimization")

    try:
        return optimize_route(request.villages, source_location=request.source_location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/workflow")
def run_workflow(request: WorkflowRequest) -> dict[str, object]:
    """
    End-to-end workflow for the product demo:
    plan -> validate -> optimize -> summarize
    """
    if not request.villages:
        raise HTTPException(status_code=400, detail="At least one village is required")

    plan_result = build_plan(request.villages, source=request.source_location)
    validation_result = run_validation_agent(
        plan_result.get("matched_villages", []),
        source_location=request.source_location,
    )
    optimization_result = optimize_route(
        validation_result.get("validated_villages", []),
        source_location=request.source_location,
    )

    summary = {
        "total_requested": len(request.villages),
        "total_matched": plan_result.get("total_matched", 0),
        "total_suggested": plan_result.get("total_suggested", 0),
        "total_unresolved": len(plan_result.get("unresolved_villages", [])),
        "validated_count": len(validation_result.get("validated_villages", [])),
        "route_length": optimization_result.get("route_length", 0),
        "total_distance_km": optimization_result.get("total_distance_km", 0),
        "estimated_time_hours": optimization_result.get("estimated_time_hours", 0),
        "clarification_needed": validation_result.get("clarification_needed", False),
    }

    llm_summary = ""
    if request.use_llm_summary:
        llm_summary = (
            "LLM hook enabled: the system is ready for a natural-language summary layer. "
            "The core deterministic workflow is already running and the next integration step is "
            "a prompt-based narrative summary."
        )

    return {
        "plan": plan_result,
        "validation": validation_result,
        "optimization": optimization_result,
        "summary": summary,
        "llm_summary": llm_summary,
    }


@app.post("/plan-text")
def plan_text(request: NaturalLanguageRequest) -> dict[str, object]:
    """Parse a natural-language route request and resolve villages using the retrieval layer."""
    request_text = request.request_text.strip()
    if not request_text:
        raise HTTPException(status_code=400, detail="Request text is required")

    intent = IntentParser.parse(request_text)
    retrieval = VillageRetrievalService()

    session_id = "session-123"
    resolved_candidates = []
    for village_name in intent.destinations:
        candidates = retrieval.retrieve_candidates(village_name, threshold=0.5, limit=5)
        candidate_summary = retrieval.build_candidate_summary(candidates)
        resolved_candidates.append({
            "input_name": village_name,
            "candidates": candidate_summary,
        })

    ambiguous = [item for item in resolved_candidates if len(item["candidates"]) > 1]
    if ambiguous:
        return {
            "status": "clarification_required",
            "session_id": session_id,
            "question": "We found multiple possible matches. Please choose the correct location for each ambiguous village.",
            "options": [
                {
                    "id": f"{session_id}-{idx}",
                    "input_name": item["input_name"],
                    "candidates": item["candidates"],
                }
                for idx, item in enumerate(ambiguous)
            ],
            "request": {
                "origin": intent.origin,
                "destinations": intent.destinations,
                "travel_intent": intent.travel_intent,
                "optimization_goal": intent.optimization_goal,
            },
        }

    return {
        "status": "planning",
        "session_id": session_id,
        "request": {
            "origin": intent.origin,
            "destinations": intent.destinations,
            "travel_intent": intent.travel_intent,
            "optimization_goal": intent.optimization_goal,
        },
        "resolved_villages": resolved_candidates,
    }


@app.post("/clarification")
def clarify_selection(request: ClarificationRequest) -> dict[str, object]:
    """Resume the workflow after the user selects a candidate option."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session id is required")
    if not request.selected_option_id:
        raise HTTPException(status_code=400, detail="Selected option id is required")

    return {
        "status": "confirmed",
        "session_id": request.session_id,
        "message": "The user-selected location is accepted. The route engine can now continue with confirmed destinations.",
        "selected_option_id": request.selected_option_id,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health endpoint for deployment and monitoring."""
    return {"status": "ok"}


@app.get("/ui", response_class=HTMLResponse)
def route_ui() -> str:
    """Serve a simple browser UI for the end-to-end workflow demo."""
    return """
    <html>
      <head>
        <title>Agentic Geospatial Route Planner</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fb; color: #1f2937; }
          .container { max-width: 980px; margin: 0 auto; }
          .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); margin-top: 20px; }
          textarea, input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; margin-top: 8px; }
          button { background: #2563eb; color: white; border: none; border-radius: 8px; padding: 12px 18px; cursor: pointer; margin-top: 12px; }
          pre { white-space: pre-wrap; background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; overflow-x: auto; }
          .status { font-weight: bold; color: #0f766e; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="card">
            <h1>Route Planner</h1>
            <p>Plan → Validate → Optimize</p>
            <label>Source Location</label>
            <input id="source" value="Hyderabad" />
            <label>Villages (one per line)</label>
            <textarea id="villages" rows="6">Balapur
Mallapur
Kothur</textarea>
            <button onclick="runWorkflow()">Run workflow</button>
            <div id="status" class="status"></div>
          </div>

          <div class="card">
            <h2>Results</h2>
            <pre id="result">Waiting for input...</pre>
          </div>
        </div>

        <script>
          async function runWorkflow() {
            const source = document.getElementById('source').value || 'Unknown';
            const villagesText = document.getElementById('villages').value;
            const villages = villagesText.split(/\n|,/).map(v => v.trim()).filter(Boolean);
            const status = document.getElementById('status');
            const result = document.getElementById('result');

            status.textContent = 'Running workflow...';
            result.textContent = '';

            try {
              const response = await fetch('/workflow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_location: source, villages, use_llm_summary: false })
              });

              const data = await response.json();
              if (!response.ok) {
                throw new Error(data.detail || 'Workflow failed');
              }

              status.textContent = 'Workflow complete';
              result.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
              status.textContent = 'Workflow failed';
              result.textContent = error.message;
            }
          }
        </script>
      </body>
    </html>
    """

