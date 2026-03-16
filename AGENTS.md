# AGENTS.md - Agentic Coding Guidelines

This document provides guidelines for agentic coding tools operating in this repository.

## Project Overview

Python-based command-line agent using LangChain, LangGraph, and Groq API to answer natural language questions about SQLite/MySQL databases.

## Key Technologies

- **Python 3.12+**, **LangChain & LangGraph**, **Groq**, **SQLite/MySQL**, **uv** (package manager)

## Build, Lint, and Test Commands

### Installation

```bash
uv venv
uv pip install -e .
pip install -e .     # Alternative
```

### Running

```bash
python main.py
```

### Testing

**No formal test suite exists.** To add tests:

```bash
pytest tests/
pytest tests/test_file.py
pytest tests/test_file.py::test_function_name
pytest -v
pytest --cov=src --cov-report=html
```

### Linting

**No linting config exists.** To add:

```bash
ruff check src/
ruff format src/
mypy src/
```

## Code Style

### Imports

Use absolute imports, grouped: stdlib, third-party, local. Sort alphabetically.

```python
import logging
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from src.config import GROQ_API_KEY
```

### Formatting

- 4 spaces indentation (no tabs)
- Max line length: 100 (soft), 120 (max)
- Blank lines separate logical sections
- Two blank lines between top-level definitions

### Naming

- **Variables/Functions**: snake_case (`get_db_connection`)
- **Classes**: PascalCase (`AgentState`)
- **Constants**: UPPER_SNAKE_CASE (`LOG_FILE`)
- **Private**: prefix underscore (`_internal_function`)

### Type Hints

Use type hints consistently. Use TypedDict for complex types:

```python
from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    messages: Annotated[List[Any], operator.add]
    db_schema: Dict[str, Any]
    current_sql: str
```

### Error Handling

Use try/except for operations that may fail. Provide meaningful error messages. Log errors. Return error state in agent state rather than raising for recoverable errors.

### Logging

```python
logger = logging.getLogger("sql_agent")
logger.info("Normal operation info")
logger.error("Error message")
```

### Agent/LangGraph

Use `StateGraph` for agent workflows. Define state using TypedDict. Use `add_node`, `add_edge`, `add_conditional_edges`. Log state transitions.

```python
workflow = StateGraph(AgentState)
workflow.add_node("get_schema", get_schema)
workflow.add_edge("get_schema", "query_understanding")
workflow.set_entry_point("get_schema")
app = workflow.compile()
```

### Database

Use connection pooling or proper connection management. Close connections in finally blocks. Use parameterized queries.

### File Structure

```
src/
├── __init__.py
├── config.py
├── database.py
└── agent/
    ├── __init__.py
    ├── graph.py
    ├── state.py
    └── prompts.py
scripts/
├── db_initiator.py
main.py
```

### Configuration

Store secrets in `.env` (do not commit). Use `python-dotenv`.

```
GROQ_API_KEY=your_key
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost
DB_NAME=databasename
DB_PORT=3306
```

### Dependencies

Add to `pyproject.toml`. Run `uv pip install -e .` after modifying.

## Common Tasks

### Add Agent Node

1. Define node function in `src/agent/graph.py`
2. Add type hints using `AgentState`
3. Return dictionary with state updates
4. Add node: `workflow.add_node("name", function)`
5. Add edges to/from the new node

### Modify Schema

1. Update `src/database.py` with schema changes
2. Update initialization logic in `initialize_db()`
3. Update prompts in `src/agent/prompts.py` if needed

## Notes

- Project uses MySQL as primary database (`src/database.py`)
- SQLite code in `scripts/db_initiator.py`
- Agent uses retry logic (max 3 attempts) for recoverable SQL errors
- Agent interactions logged to `agent_interactions.log`
- No formal test suite exists
