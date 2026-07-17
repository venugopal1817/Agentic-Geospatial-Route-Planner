"""
Validation Agent: LangGraph-based multi-agent workflow for village validation.

This demonstrates:
- State management across agents
- Conditional branching based on validation results
- Agent orchestration using LangGraph
"""

from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, START, END
from app.services.validator import VillageValidator, validate_village_batch_for_routing, ValidationResult


class ValidationState(TypedDict):
    """State passed between validation agents"""
    
    # Input
    matched_villages: List[Dict]  # Villages from matching engine
    source_location: str
    
    # Processing
    validation_results: Optional[Dict] = None  # {valid, warnings, invalid}
    confidence_threshold: float  # Default 0.5
    
    # Output
    validated_villages: List[ValidationResult] = []
    clarification_needed: bool = False
    clarification_message: str = ""
    status: str = "pending"  # pending, validating, clarifying, complete, failed


class ValidationAgent:
    """
    LangGraph-based agent for multi-source village validation.
    
    Workflow:
    START → validate_villages → decide_clarity → (clarify or continue) → END
    """
    
    def __init__(self, use_osm: bool = False):
        """
        Initialize validation agent.
        
        Args:
            use_osm: Whether to use OpenStreetMap cross-validation (slower but more thorough)
        """
        self.use_osm = use_osm
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Construct the LangGraph workflow"""
        graph_builder = StateGraph(ValidationState)
        
        # Add nodes (agent functions)
        graph_builder.add_node("validate_villages", self._validate_villages_node)
        graph_builder.add_node("check_clarity", self._check_clarity_node)
        graph_builder.add_node("clarify_user", self._clarify_user_node)
        graph_builder.add_node("finalize", self._finalize_node)
        
        # Define edges
        # START → validate_villages
        graph_builder.add_edge(START, "validate_villages")
        
        # validate_villages → check_clarity
        graph_builder.add_edge("validate_villages", "check_clarity")
        
        # check_clarity has conditional routing
        graph_builder.add_conditional_edges(
            "check_clarity",
            self._route_clarity_check,
            {
                "clarify": "clarify_user",
                "continue": "finalize"
            }
        )
        
        # clarify_user → finalize
        graph_builder.add_edge("clarify_user", "finalize")
        
        # finalize → END
        graph_builder.add_edge("finalize", END)
        
        return graph_builder.compile()
    
    def _validate_villages_node(self, state: ValidationState) -> ValidationState:
        """
        Node 1: Validate all matched villages.
        
        Updates state with:
        - validation_results: {valid, warnings, invalid}
        - status: "validating"
        """
        validator = VillageValidator()
        state["validation_results"] = validate_village_batch_for_routing(
            state["matched_villages"],
            use_osm_validation=self.use_osm
        )
        state["status"] = "validating"
        
        # Flatten all results for easy access
        all_results = (
            state["validation_results"]["valid"] +
            state["validation_results"]["warnings"] +
            state["validation_results"]["invalid"]
        )
        state["validated_villages"] = all_results
        
        return state
    
    def _check_clarity_node(self, state: ValidationState) -> ValidationState:
        """
        Node 2: Check if results are clear or ambiguous.
        
        If all villages have high confidence, proceed normally.
        If some have low confidence, may need clarification.
        """
        results = state["validation_results"]
        
        invalid_count = len(results["invalid"])
        warning_count = len(results["warnings"])
        
        # Determine if we need user clarification
        # Rule: If > 30% of results have warnings or are invalid, ask user
        total = len(state["matched_villages"])
        ambiguous_count = invalid_count + warning_count
        
        if total > 0 and (ambiguous_count / total) > 0.3:
            state["clarification_needed"] = True
            state["clarification_message"] = (
                f"Validation found issues with {ambiguous_count}/{total} locations. "
                f"({warning_count} low confidence, {invalid_count} invalid). "
                "Please review and confirm."
            )
        else:
            state["clarification_needed"] = False
        
        return state
    
    def _route_clarity_check(self, state: ValidationState) -> str:
        """
        Routing function: Decide whether to ask user or continue.
        """
        if state["clarification_needed"]:
            return "clarify"
        return "continue"
    
    def _clarify_user_node(self, state: ValidationState) -> ValidationState:
        """
        Node 3: Ask user for clarification on ambiguous results.
        
        In production, this would be an interactive prompt.
        For now, we log it and mark as "clarifying".
        """
        state["status"] = "clarifying"
        
        # In a real system, this would:
        # 1. Send message to user interface
        # 2. Wait for user input
        # 3. Update validated_villages based on user choice
        
        # For now, just log
        print(f"[CLARIFICATION NEEDED] {state['clarification_message']}")
        
        # Bias towards keeping high-confidence results
        state["validated_villages"] = state["validation_results"]["valid"]
        
        return state
    
    def _finalize_node(self, state: ValidationState) -> ValidationState:
        """
        Node 4: Finalize validation results.
        
        Prepare output for downstream agents (geo retrieval, route optimization).
        """
        state["status"] = "complete"
        
        # Summary
        valid_count = len(state["validation_results"]["valid"])
        total_count = len(state["matched_villages"])
        
        print(f"[VALIDATION COMPLETE] {valid_count}/{total_count} villages validated successfully")
        
        return state
    
    def validate(self, matched_villages: List[Dict], source_location: str = "Unknown") -> Dict:
        """
        Run the validation workflow.
        
        Args:
            matched_villages: Output from the Planner agent (list of matched villages)
            source_location: Starting location for context
        
        Returns:
            Final state with validated_villages and confidence scores
        """
        initial_state = ValidationState(
            matched_villages=matched_villages,
            source_location=source_location,
            confidence_threshold=0.5
        )
        
        result = self.graph.invoke(initial_state)
        
        return {
            "status": result["status"],
            "validated_villages": [
                {
                    "name": v.name,
                    "canonical_name": v.canonical_name,
                    "district": v.district,
                    "subdistric": v.subdistric,
                    "latitude": v.latitude,
                    "longitude": v.longitude,
                    "confidence_score": v.confidence_score,
                    "is_valid": v.is_valid,
                    "validation_source": v.validation_source,
                    "warnings": v.warnings
                }
                for v in result["validated_villages"]
            ],
            "clarification_needed": result["clarification_needed"],
            "clarification_message": result.get("clarification_message", "")
        }


# Convenience function for API integration
def run_validation_agent(matched_villages: List[Dict], source_location: str = "Unknown") -> Dict:
    """
    Quick-access function to run validation without instantiating the agent.
    """
    agent = ValidationAgent(use_osm=False)  # OSM disabled for speed in MVP
    return agent.validate(matched_villages, source_location)
