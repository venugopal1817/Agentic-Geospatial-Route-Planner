# LangGraph Learning Roadmap for Validation Agent

## What is LangGraph?

LangGraph is a framework for building **stateful, multi-agent workflows**. It extends LangChain with graph-based state management and agent orchestration.

**Key concepts:**
- **State**: The shared data structure passed between agents
- **Nodes**: Agent functions that process state
- **Edges**: Transitions between agents (conditional or deterministic)
- **Graph**: The complete workflow definition

---

## Why LangGraph for This Project

Your project has:
- Multiple agents (Planner, Village Validation, Geo Retrieval, Route Optimization, Map Generation)
- Complex state passing between agents
- Conditional logic (e.g., "ask user for clarification if ambiguous")
- Need to retry or branch based on intermediate results

LangGraph handles all of this elegantly.

---

## Essential Learning Resources (In Order)

### **1. Official LangGraph Docs** (1-2 hours)
- Start: https://langchain-ai.github.io/langgraph/
- Read sections:
  - **Concepts** → Understand State, Nodes, Edges
  - **Tutorials** → Basic Agent Loop
  - **How-to Guides** → State Management, Conditional Edges

### **2. Core Concepts to Understand** (30 mins)

#### **State Graph**
```python
from langgraph.graph import StateGraph, START, END

# Define your state type (what data flows between agents)
state_schema = {
    "input": str,
    "village_matches": list,
    "validation_results": dict,
    "confidence_score": float
}

# Create graph
graph_builder = StateGraph(state_schema)
```

#### **Adding Nodes** (Agent Functions)
```python
def validation_node(state):
    """A node is just a function that takes state and returns updated state"""
    # Process state
    state["validation_results"] = validate(state["village_matches"])
    return state

# Add to graph
graph_builder.add_node("validate", validation_node)
```

#### **Defining Edges** (Transitions)
```python
# Simple edge: A → B
graph_builder.add_edge("validate", "geo_retrieval")

# Conditional edge: depends on state
def decide_next_node(state):
    if state["confidence_score"] < 0.5:
        return "ask_user"
    return "geo_retrieval"

graph_builder.add_conditional_edges(
    "validate",
    decide_next_node
)

# Start and end
graph_builder.add_edge(START, "validate")
graph_builder.add_edge("geo_retrieval", END)
```

### **3. Code Examples to Run** (1 hour)

**Example 1: Simple Sequential Workflow**
```python
from langgraph.graph import StateGraph, START, END

class State:
    def __init__(self):
        self.messages = []

def node_1(state):
    state.messages.append("Step 1")
    return state

def node_2(state):
    state.messages.append("Step 2")
    return state

graph = StateGraph(State)
graph.add_node("step1", node_1)
graph.add_node("step2", node_2)
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)

compiled = graph.compile()
result = compiled.invoke({})
```

**Example 2: Conditional Branching**
```python
def router_node(state):
    if len(state.messages) > 2:
        return "branch_a"
    return "branch_b"

graph.add_conditional_edges("step1", router_node)
```

**Example 3: Loop/Retry Logic**
```python
def should_continue(state):
    if state.retry_count < 3:
        return "retry"
    return END

graph.add_conditional_edges("process", should_continue)
graph.add_edge("retry", "process")
```

### **4. Key Patterns for Our Use Case** (30 mins)

#### **Pattern 1: Sequential Agents**
```
START → Validation → Geo Retrieval → Route Optimization → Response → END
```

#### **Pattern 2: Conditional Disambiguation**
```
START → Validation → {
    if confident → Geo Retrieval
    if ambiguous → Ask User → Clarify → Geo Retrieval
} → END
```

#### **Pattern 3: Retry with Fallback**
```
START → Primary Source → {
    if success → Continue
    if failure → Fallback Source → Continue
} → END
```

---

## What You'll Learn Building the Validation Agent

1. **State Management** — How to pass data between agents
2. **Node Definition** — Writing agent functions that fit into a graph
3. **Conditional Logic** — Branching based on intermediate results
4. **Error Handling** — Fallback strategies when validation fails
5. **Testing Graphs** — Unit testing multi-node workflows

---

## Quick Start: Validation Agent Structure

```
app/
  services/
    planner.py (existing)
    validator.py (NEW - single validation functions)
    
  agents/
    validation_agent.py (NEW - LangGraph workflow)
    
tests/
  test_validation_agent.py (NEW)
  test_validator.py (NEW)
```

---

## Resources to Bookmark

1. **LangGraph Official**: https://langchain-ai.github.io/langgraph/
2. **LangChain Discord**: Community support channel
3. **GitHub Examples**: https://github.com/langchain-ai/langgraph/tree/main/examples
4. **State Management Deep Dive**: https://langchain-ai.github.io/langgraph/concepts/low_level_concept_guide/

---

## Study Plan (Recommended)

**Day 1:**
- Read LangGraph Concepts (1 hour)
- Run Example 1 & 2 locally (1 hour)

**Day 2:**
- Read State Management guide (1 hour)
- Run Example 3 with retry logic (1 hour)

**Day 3:**
- Start building Validation Agent with LangGraph (ongoing)

---

## Questions to Ask Yourself as You Learn

1. **What state do I need to pass between agents?**
   - For Validation Agent: village matches + validation results + confidence scores

2. **What are the possible paths through my workflow?**
   - Success path: validation → geo retrieval
   - Failure path: validation fails → ask user → clarify
   - Fallback path: primary source fails → try secondary source

3. **When should I branch conditionally?**
   - After validation: if confidence < threshold → ask user
   - After geo retrieval: if no coordinates → fallback to manual entry

4. **How do I unit test this?**
   - Mock the agents
   - Test state transitions
   - Test conditional edge logic

---

## Next: Implementation

Ready to build! I'll start with:

1. **app/services/validator.py** — Pure validation functions (no LangGraph yet)
2. **app/agents/validation_agent.py** — LangGraph workflow wrapping validator functions
3. **tests/test_validation_agent.py** — Test the graph transitions
4. Integration into main API

Let's go! 🚀
