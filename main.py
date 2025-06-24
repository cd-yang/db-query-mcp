# server.py
import logging
import sqlite3

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.prompt()
def example_prompt(code: str) -> str:
    return f"Please review this code:\n\n{code}"


# @mcp.tool()
# def calculate_bmi(weight_kg: float, height_m: float) -> float:
#     """Calculate BMI given weight in kg and height in meters"""
#     return weight_kg / (height_m**2)


@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely for 装备数据库."""
    logging.info(f"Executing SQL query: {sql}")
    conn = sqlite3.connect(
        "./resource/DB3K_DFKY_decrypt.db")
    try:
        result = conn.execute(sql).fetchall()
        conn.commit()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting server...")
    mcp.run(transport='stdio')
