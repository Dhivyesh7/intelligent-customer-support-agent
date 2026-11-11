from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "support_tickets.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                category TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                priority TEXT NOT NULL,
                needs_human_review INTEGER NOT NULL,
                suggested_response TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def insert_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO tickets (
                id, subject, description, customer_email, category, sentiment, priority,
                needs_human_review, suggested_response, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ticket["id"], ticket["subject"], ticket["description"], ticket["customer_email"],
                ticket["category"], ticket["sentiment"], ticket["priority"],
                int(ticket["needs_human_review"]), ticket["suggested_response"],
                ticket["status"], ticket["created_at"],
            ),
        )
    return ticket


def list_tickets() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM tickets ORDER BY created_at DESC").fetchall()
    tickets = [dict(row) for row in rows]
    for ticket in tickets:
        ticket["needs_human_review"] = bool(ticket["needs_human_review"])
    return tickets


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        return None
    ticket = dict(row)
    ticket["needs_human_review"] = bool(ticket["needs_human_review"])
    return ticket


def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id)
        )
        if cursor.rowcount == 0:
            return None
    return get_ticket(ticket_id)
