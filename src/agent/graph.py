import json
import logging
import re
from datetime import datetime

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from src.agent.prompts import (
    query_understanding_prompt,
    sql_generation_prompt,
    table_inspection_prompt,
    table_selection_prompt,
)
from src.agent.state import AgentState
from src.config import GROQ_API_KEY
from src.database import db, get_db_connection

logger = logging.getLogger("sql_agent")

# Initialize LLM and Toolkit
# llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key=GROQ_API_KEY)
llm = ChatOllama(model="qwen3.5:4b", temperature=0, base_url="http://192.168.68.144:11434")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Logging functions
def log_interaction(state: AgentState, direction: str):
    logger.info(f"[{direction}] Attempt: {state.get('attempt_count', 1)}, "
                f"SQL: {state.get('current_sql', 'N/A')[:100]}, "
                f"Error: {state.get('error', 'None')}")

def log_execution(state: AgentState):
    logger.info(f"[EXECUTE] SQL: {state.get('current_sql', '')[:200]}, "
                f"Error: {state.get('error', 'None')}, "
                f"Attempt: {state.get('attempt_count', 1)}")

# Node functions
def get_schema(state: AgentState):
    logger.info("Retrieving database schema")
    table_names = db.get_usable_table_names()
    logger.info(f"Available tables: {table_names}")
    return {"db_schema": table_names, "available_tables": table_names}

def select_tables(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else last_message.get("content", "")
    
    logger.info("Selecting relevant tables for the query")
    chain = table_selection_prompt | llm | StrOutputParser()
    
    available_tables_str = "\n".join([f"- {t}" for t in state.get("available_tables", [])])
    previous_queries = "\n".join(state.get("previous_queries", []))
    
    # Include previously tried tables to avoid repetition
    tried_tables = state.get("selected_tables", [])
    retry_context = ""
    if tried_tables:
        retry_context = f"\n\nNOTE: The following tables were already tried but didn't work: {', '.join(tried_tables)}\nPlease try different tables or a different approach."
    
    result = chain.invoke({
        "query": query,
        "available_tables": available_tables_str + retry_context,
        "previous_queries": previous_queries
    })
    
    logger.info(f"Table selection result: {result}")
    
    # Parse the result to extract table names
    selected = []
    reasoning = ""
    lines = result.split('\n')
    for line in lines:
        if line.startswith("TABLES:"):
            tables_str = line.replace("TABLES:", "").strip()
            selected = [t.strip() for t in tables_str.split(",")]
        elif line.startswith("REASONING:"):
            reasoning = line.replace("REASONING:", "").strip()
    
    logger.info(f"Selected tables: {selected}")
    
    # Clear current_sql so new SQL gets generated
    return {"selected_tables": selected, "analysis": reasoning, "current_sql": ""}

def inspect_tables(state: AgentState):
    selected_tables = state.get("selected_tables", [])
    logger.info(f"Inspecting tables: {selected_tables}")
    
    table_schemas = {}
    for table in selected_tables:
        try:
            info = db.get_table_info([table])
            table_schemas[table] = info
            logger.info(f"Table {table} info: {info[:200]}...")
        except Exception as e:
            logger.warning(f"Could not get info for table {table}: {e}")
            table_schemas[table] = f"Error: {str(e)}"
    
    # Format schema for prompt
    schema_str = ""
    for table, info in table_schemas.items():
        schema_str += f"\n\n=== {table} ===\n{info}"
    
    return {"db_schema": table_schemas, "table_schemas": schema_str}

def query_understanding(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else last_message.get("content", "")
    log_interaction(state, "user_input")
    chain = query_understanding_prompt | llm | StrOutputParser()
    analysis = chain.invoke({
        "query": query,
        "db_schema": state["db_schema"],
        "previous_queries": "\n".join(state["previous_queries"])
    })
    logger.info(f"Query analysis: {analysis}")
    return {"analysis": analysis, "messages": messages + [AIMessage(content=analysis)]}

def generate_sql(state: AgentState):
    query = state["messages"][0].content
    chain = sql_generation_prompt | llm | StrOutputParser()
    sql_query = chain.invoke({
        "query": query,
        "analysis": state["analysis"],
        "db_schema": state["db_schema"],
        "previous_queries": "\n".join(state["previous_queries"])
    })
    sql_query = sql_query.strip()
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:-3].strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query[3:-3].strip()
    sql_query = re.sub(r'^.*?(SELECT|CREATE|INSERT|UPDATE|DELETE)', r'\1', sql_query, flags=re.IGNORECASE | re.DOTALL)
    sql_query = sql_query.split(';')[0].strip() + ';'
    logger.info(f"Generated SQL: {sql_query}")
    return {"current_sql": sql_query}

def execute_sql(state: AgentState):
    sql_query = state["current_sql"]
    attempt_count = state.get("attempt_count", 1)
    logger.info(f"Executing SQL (attempt {attempt_count}): {sql_query}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            result = {"columns": columns, "rows": rows}
        else:
            conn.commit()
            result = f"Query executed successfully. {cursor.rowcount} rows affected."
        conn.close()
        execution_result = {"execution_result": {"result": result, "query": sql_query}, "error": None, "attempt_count": attempt_count}
        log_execution({**state, **execution_result})
        return execution_result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"SQL Execution Error: {error_msg}")
        # Keep original error for retry logic
        original_error = error_msg
        error_details = parse_sqlite_error(error_msg)
        error_result = {"execution_result": None, "error": error_details, "original_error": original_error, "attempt_count": attempt_count + 1}
        log_execution({**state, **error_result})
        return error_result

def parse_sqlite_error(error_msg: str) -> str:
    error_mapping = {
        "no such table": "The table you're trying to access doesn't exist",
        "no such column": "One of the columns you're trying to use doesn't exist",
        "syntax error": "There's a syntax error in the SQL query",
        "UNIQUE constraint failed": "You're trying to insert a duplicate value that must be unique",
        "FOREIGN KEY constraint failed": "The value you're trying to use doesn't exist in the referenced table",
        "table .* already exists": "A table with this name already exists",
        "no column named": "A column you're trying to use doesn't exist",
        "ambiguous column name": "A column name is ambiguous - it exists in multiple tables"
    }
    for pattern, friendly_msg in error_mapping.items():
        if re.search(pattern, error_msg, re.IGNORECASE):
            return friendly_msg
    return error_msg

def check_data_availability(state: AgentState) -> str:
    """Check if the query result has data or if we need to search other tables."""
    result = state.get("execution_result", {}).get("result")
    error = state.get("original_error") or state.get("error")  # Use original error for retry checks
    attempt = state.get("attempt_count", 1)
    max_attempts = state.get("max_attempts", 3)
    
    logger.info(f"Checking data availability - attempt: {attempt}, max: {max_attempts}, error: {error}, result: {result}")
    
    # If there's an error and we can retry
    if error:
        if attempt >= max_attempts:
            logger.info(f"Max attempts reached ({max_attempts}), giving up")
            return "generate_response"
        # Check if it's a retryable error (use original error)
        retryable_errors = ["no such table", "no such column", "syntax error", "table .* already exists", "no column named", "ambiguous column name"]
        if any(re.search(p, str(error).lower()) for p in retryable_errors):
            logger.info(f"Retryable error detected, going back to select_tables")
            return "select_tables"
        logger.info(f"Non-retryable error, generating response")
        return "generate_response"
    
    # If result is empty but query was a SELECT, we might need more tables
    if isinstance(result, dict) and "rows" in result:
        if len(result.get("rows", [])) == 0 and attempt < max_attempts:
            logger.info("Empty result - might need to search other tables")
            return "select_tables"
    
    logger.info("Result available, generating response")
    return "generate_response"

def should_retry(state: AgentState) -> str:
    return check_data_availability(state)

def generate_response(state: AgentState):
    if state.get("error"):
        if state.get("attempt_count", 1) >= state.get("max_attempts", 3):
            response = f"I'm sorry, I couldn't complete your request after multiple attempts. Error: {state['error']}"
        else:
            response = f"I ran into an issue: {state['error']}. I'll try to fix it (attempt {state.get('attempt_count', 1)})."
    else:
        result = state["execution_result"]["result"]
        
        # Build detailed response
        response = "## Query Results\n\n"
        
        # Show tables inspected
        selected = state.get("selected_tables", [])
        if selected:
            response += f"**Tables inspected:** {', '.join(selected)}\n\n"
        
        # Show reasoning
        analysis = state.get("analysis", "")
        if analysis:
            response += f"**Analysis:** {analysis}\n\n"
        
        # Show SQL query
        sql = state.get("current_sql", "")
        if sql:
            response += f"**SQL Query:**\n```sql\n{sql}\n```\n\n"
        
        # Show results
        if isinstance(result, dict) and "columns" in result:
            response += "**Results:**\n\n"
            response += "\t".join(result["columns"]) + "\n"
            for row in result["rows"][:10]:
                response += "\t".join(str(item) for item in row) + "\n"
            if len(result["rows"]) > 10:
                response += f"\n(Showing first 10 of {len(result['rows'])} rows)\n"
        else:
            response += f"**Status:** {result}"
    
    logger.info(f"Agent response: {response}")
    new_state = {**state, "messages": state["messages"] + [AIMessage(content=response)], "previous_queries": state["previous_queries"] + [state["messages"][0].content]}
    log_interaction(new_state, "agent_response")
    return {"messages": new_state["messages"], "previous_queries": new_state["previous_queries"]}

# Graph construction
workflow = StateGraph(AgentState)
workflow.add_node("get_schema", get_schema)
workflow.add_node("select_tables", select_tables)
workflow.add_node("inspect_tables", inspect_tables)
workflow.add_node("query_understanding", query_understanding)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.add_node("generate_response", generate_response)

# Edges
workflow.add_edge("get_schema", "select_tables")
workflow.add_edge("select_tables", "inspect_tables")
workflow.add_edge("inspect_tables", "query_understanding")
workflow.add_edge("query_understanding", "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")

# Conditional edges from execute_sql
workflow.add_conditional_edges(
    "execute_sql", 
    should_retry, 
    {
        "select_tables": "select_tables",  # Retry with different tables
        "generate_response": "generate_response"
    }
)

workflow.add_edge("generate_response", END)
workflow.set_entry_point("get_schema")
app = workflow.compile()

def run_agent(query: str):
    logger.info(f"Starting new agent interaction with query: {query}")
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "db_schema": "",
        "previous_queries": [],
        "current_sql": "",
        "execution_result": None,
        "error": None,
        "original_error": "",
        "attempt_count": 1,
        "max_attempts": 3,
        "analysis": "",
        "available_tables": [],
        "selected_tables": []
    }
    result = app.invoke(initial_state)
    logger.info("Agent interaction completed")
    return result["messages"][-1].content
