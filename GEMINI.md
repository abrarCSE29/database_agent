# Project Overview

This project is a Python-based command-line agent that uses LangChain, LangGraph, and the Groq API to answer natural language questions about a SQLite database. The agent can understand user queries, generate SQL, execute it against the database, and return the results in a human-readable format.

## Key Technologies

*   **Python:** The core programming language.
*   **LangChain & LangGraph:** Used to build the agent and define the workflow.
*   **Groq:** Provides the language model for understanding and generating SQL.
*   **SQLite:** The database engine.

# Getting Started

## Prerequisites

*   Python 3.12+
*   `uv` package manager (or `pip`)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd database-agent
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    uv pip install -r requirements.txt 
    ```
    *(Note: A `requirements.txt` does not exist. This is inferred from `pyproject.toml`)*

## Configuration

1.  Create a `.env` file in the root of the project.
2.  Add your Groq API key to the `.env` file:
    ```
    GROQ_API_KEY=your_groq_api_key
    ```

# Building and Running

To run the agent, execute the following command:

```bash
python agent.py
```

This will start an interactive command-line interface. You can then ask questions about the database.

**Example questions:**

*   Show me all region names
*   Create a table showing total orders by region
*   Which region has the highest total sales?

To exit the agent, type `quit`.

# Development Conventions

*   The main application logic is in `agent.py`.
*   The project uses `pyproject.toml` to manage dependencies.
*   A `uv.lock` file is present, indicating `uv` is used for package management.
*   The `main.py` file is a simple entry point and does not contain the main application logic.
*   Agent interactions are logged to `agent_interactions.log`.
*   The database is automatically created and seeded with sample data in `example.db` if it does not exist.
