import sqlite3
from utils import tool

DB_PATH = "example.db"

def get_db():
    return sqlite3.connect(DB_PATH)

@tool
def list_tables():
    """List all table names in the SQLite database."""
    conn = get_db()
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return {"tables": tables}


@tool
def list_columns(table_name: str):
    """List column names and types for a table."""
    conn = get_db()
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    cols = [{"name": r[1], "type": r[2]} for r in cur.fetchall()]
    conn.close()
    return {"columns": cols}


@tool
def preview_table(table_name: str, limit: int = 20):
    """Preview the first N rows of a table."""
    conn = get_db()
    cur = conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    conn.close()
    # Return as serializable structure
    return {
        "columns": col_names,
        "rows": [list(r) for r in rows],
    }


# @tool
# def search_roms(query: str):
#     """Search ROMs by partial match on title in 'roms' table."""
#     conn = get_db()
#     cur = conn.execute("SELECT * FROM roms WHERE title LIKE ?", (f"%{query}%",))
#     rows = cur.fetchall()
#     col_names = [desc[0] for desc in cur.description]
#     conn.close()
#     return {
#         "columns": col_names,
#         "rows": [list(r) for r in rows],
#     }
