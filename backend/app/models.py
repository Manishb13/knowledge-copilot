import json
import sqlite3
from typing import Any, Optional


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain Python dictionary."""
    return dict(row)


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert a list of sqlite3.Row objects to a list of dicts."""
    return [row_to_dict(row) for row in rows]


def parse_citations(citations_json: Optional[str]) -> list[dict]:
    """Safely parse a JSON string of citations into a list of dicts."""
    if not citations_json:
        return []
    try:
        return json.loads(citations_json)
    except (json.JSONDecodeError, TypeError):
        return []
