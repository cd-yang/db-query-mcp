import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import StdioServerParameters

from smolagents import (CodeAgent, InferenceClientModel, MCPClient,
                        OpenAIServerModel, Tool, ToolCallingAgent)

# server_parameters = StdioServerParameters(
#     # Using uvx ensures dependencies are available
#     # command="uv --directory D:\\VSCodeRepos\\db-query-mcp\\ run main.py",
#     command="uvx",  # Using uvx ensures dependencies are available
#     args=["--quiet", "pubmedmcp@0.1.3"],
#     env={"UV_PYTHON": "3.10.16", **os.environ},
# )


# model = InferenceClientModel()
model = OpenAIServerModel(
    # model_id="qwen2.5-coder:32b",
    model_id="qwen3-coder:30b",
    api_base="http://192.168.100.202:11434/v1",
    api_key="EMPTY")

# with MCPClient(server_parameters) as tools:
# with MCPClient({"url": "http://127.0.0.1:8000/mcp", "transport": "streamable-http"}) as tools:
#     agent = CodeAgent(tools=tools, model=model,
#                       stream_outputs=True, add_base_tools=True)

#     agent.run("帮我从数据库中查询 F-35 的雷达特征")


# Path to Messages database
DB_PATH = Path(os.environ.get('SQLITE_DB_PATH',
               "resource/DB3K_DFKY_decrypt.db"))


class SQLiteConnection:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()


class DatabaseQueryTool(Tool):
    name = "database_query"
    description = """
    This is a tool that can query the SQLite database.
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "the SQL query to execute",
        },
        "params": {
            "type": "array",
            "description": "the parameters for the query",
            "nullable": "True"
        },
        "fetch_all": {
            "type": "boolean",
            "description": "if True, fetches all results. If False, fetches one row.",
            "nullable": "True"
        },
        "row_limit": {
            "type": "integer",
            "description": "the maximum number of rows to return (default 1000)",
            "nullable": "True"
        }
    }
    output_type = "array"

    def forward(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        fetch_all: bool = True,
        row_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Execute a query on the Messages database.

        Args:
            query: SELECT SQL query to execute
            params: Optional list of parameters for the query
            fetch_all: If True, fetches all results. If False, fetches one row.
            row_limit: Maximum number of rows to return (default 1000)

        Returns:
            List of dictionaries containing the query results
        """
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Messages database not found at: {DB_PATH}")

        # Clean and validate the query
        query = query.strip()

        # Remove trailing semicolon if present
        if query.endswith(';'):
            query = query[:-1].strip()

        # Check for multiple statements by looking for semicolons not inside quotes
        def contains_multiple_statements(sql: str) -> bool:
            in_single_quote = False
            in_double_quote = False
            for char in sql:
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == ';' and not in_single_quote and not in_double_quote:
                    return True
            return False

        if contains_multiple_statements(query):
            raise ValueError("Multiple SQL statements are not allowed")

        # Validate query type (allowing common CTEs)
        query_lower = query.lower()
        if not any(query_lower.startswith(prefix) for prefix in ('select', 'with')):
            raise ValueError(
                "Only SELECT queries (including WITH clauses) are allowed for safety")

        params = params or []

        with SQLiteConnection(DB_PATH) as conn:
            cursor = conn.cursor()

            try:
                # Only add LIMIT if query doesn't already have one
                if 'limit' not in query_lower:
                    query = f"{query} LIMIT {row_limit}"

                cursor.execute(query, params)

                if fetch_all:
                    results = cursor.fetchall()
                else:
                    results = [cursor.fetchone()]

                return [dict(row) for row in results if row is not None]

            except sqlite3.Error as e:
                raise ValueError(f"SQLite error: {str(e)}")


database_query_tool = DatabaseQueryTool()
# agent = CodeAgent(tools=[database_query_tool], model=model,
agent = ToolCallingAgent(tools=[database_query_tool], model=model,
                         stream_outputs=True, add_base_tools=True)

# agent.run("帮我从数据库中查询 F-35 的雷达特征")
agent.run("从数据库中查询，具备发射鱼叉反舰导弹的舰艇都有哪些型号，按照列装下水年代排序？")
