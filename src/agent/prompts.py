from langchain_core.prompts import ChatPromptTemplate

table_selection_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert SQL assistant. Analyze the user's request and identify which tables in the database are needed to answer the query.

Available tables in the database:
{available_tables}

Previous queries:
{previous_queries}

Analyze the user's request and select the most relevant tables. Explain your reasoning for each selected table.

Return your response in the following format:
TABLES: table1, table2, ...
REASONING: Your explanation here"""),
    ("human", "{query}")
])

table_inspection_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert SQL assistant. Based on the user's query and selected tables, determine what columns/data is available in those tables.

User's query: {query}

Selected tables: {selected_tables}

Table schemas:
{table_schemas}

Return a structured analysis of:
1. What columns are available in the selected tables
2. How they can be used to answer the query
3. Any joins or relationships between tables that might be useful"""),
    ("human", "Analyze the available data")
])

query_understanding_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert SQL assistant. Analyze the user's request and determine:
    1. What tables are needed
    2. What operations should be performed
    3. Whether a new table should be created
    4. The structure of the new table if needed

    Current database schema:
    {db_schema}

    Previous queries:
    {previous_queries}

    Respond with a structured analysis of the query."""),
    ("human", "{query}")
])

sql_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", """Generate SQL to fulfill the user's request. Follow these rules strictly:

    1. For table creation, use: CREATE TABLE new_table_name AS SELECT ...
    2. For queries, use standard SELECT statements
    3. Always use proper JOIN syntax when combining tables
    4. Include all necessary columns in GROUP BY clauses
    5. Use proper aggregation functions (COUNT, SUM, AVG, etc.)
    6. Make sure all table and column names match the schema exactly
    7. Only return the SQL query, nothing else

    Current database schema:
    {db_schema}

    Analysis of the request:
    {analysis}

    Previous queries:
    {previous_queries}

    IMPORTANT: Your response must contain ONLY the SQL query, no other text.
    """),
    ("human", "Generate SQL for: {query}")
])
