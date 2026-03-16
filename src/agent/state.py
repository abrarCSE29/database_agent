from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    messages: Annotated[List[Any], operator.add]
    db_schema: Dict[str, Any]
    previous_queries: List[str]
    current_sql: str
    execution_result: Dict[str, Any]
    error: str
    original_error: str
    attempt_count: int
    max_attempts: int
    analysis: str
    available_tables: List[str]
    selected_tables: List[str]
