import os
import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Fake API key so the script can compile and visualize the graph without errors
os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-visualization-only"

# ==========================================
# 1. Define the Graph State
# ==========================================
class AgencyState(TypedDict):
    # Operator.add ensures messages are appended
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The supervisor will update this field to route the graph
    next_worker: str 

# ==========================================
# 2. Define the Tools
# ==========================================
@tool
def web_search(query: str):
    """Searches the internet for documentation or tech stacks."""
    return f"Search results for: {query}"

@tool
def write_code_to_file(filename: str, code: str):
    """Writes a Python script to the local disk."""
    return f"Successfully saved code to {filename}"

# ==========================================
# 3. Setup LLMs with SUBSETS of Tools (Global)
# ==========================================
base_llm = ChatOpenAI(model="gpt-4o")

# The Supervisor gets no tools. It just outputs structured data to pick the next worker.
# (In a real app, we'd use .with_structured_output() here)
supervisor_llm = base_llm 

# The Researcher ONLY gets the web search tool
researcher_tools = [web_search]
researcher_llm = base_llm.bind_tools(researcher_tools)

# The Coder ONLY gets the file writing tool
coder_tools = [write_code_to_file]
coder_llm = base_llm.bind_tools(coder_tools)

# ==========================================
# 4. Define the Logical Nodes
# ==========================================
def supervisor_node(state: AgencyState):
    """The boss. Decides whether the researcher or coder should work next."""
    # Logic goes here...
    return {"next_worker": "researcher"} # Mocked for structure

def researcher_node(state: AgencyState):
    """The researcher. Invokes the LLM bound with search tools."""
    # Logic goes here...
    return {"messages": []} # Mocked for structure

def coder_node(state: AgencyState):
    """The coder. Invokes the LLM bound with coding tools."""
    # Logic goes here...
    return {"messages": []} # Mocked for structure

# Create specific Tool Nodes for visual hierarchy
research_tools_node = ToolNode(researcher_tools)
coding_tools_node = ToolNode(coder_tools)

# ==========================================
# 5. Define Routing Logic (Conditional Edges)
# ==========================================
def supervisor_router(state: AgencyState) -> str:
    """Routes based on what the supervisor decided."""
    return state.get("next_worker", "FINISH")

def researcher_router(state: AgencyState) -> str:
    """If the researcher used a tool, go to its tool node. Otherwise, report back to supervisor."""
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "research_tools"
    return "supervisor"

def coder_router(state: AgencyState) -> str:
    """If the coder used a tool, go to its tool node. Otherwise, report back to supervisor."""
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "coding_tools"
    return "supervisor"

# ==========================================
# 6. Build and Compile the Graph
# ==========================================
builder = StateGraph(AgencyState)

# Add all nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("coder", coder_node)
builder.add_node("research_tools", research_tools_node)
builder.add_node("coding_tools", coding_tools_node)

# Flow: Start -> Supervisor
builder.add_edge(START, "supervisor")

# Flow: Supervisor delegates (or finishes)
# Note: The dictionary at the end is required for the visualizer to draw the paths!
builder.add_conditional_edges(
    "supervisor", 
    supervisor_router,
    {"researcher": "researcher", "coder": "coder", "FINISH": END}
)

# Flow: Researcher's internal loop
builder.add_conditional_edges(
    "researcher",
    researcher_router,
    {"research_tools": "research_tools", "supervisor": "supervisor"}
)
builder.add_edge("research_tools", "researcher") # Loop back to researcher after tool finishes

# Flow: Coder's internal loop
builder.add_conditional_edges(
    "coder",
    coder_router,
    {"coding_tools": "coding_tools", "supervisor": "supervisor"}
)
builder.add_edge("coding_tools", "coder") # Loop back to coder after tool finishes

graph = builder.compile()

# ==========================================
# 7. Visualize and Save
# ==========================================
if __name__ == "__main__":
    print("Generating hierarchical agency visualization...")
    
    # Draw graph and save as PNG
    image_data = graph.get_graph().draw_mermaid_png()
    output_filename = "hierarchical_agency.png"
    
    with open(output_filename, "wb") as f:
        f.write(image_data)
        
    print(f"Success! Graph saved as '{output_filename}'.")