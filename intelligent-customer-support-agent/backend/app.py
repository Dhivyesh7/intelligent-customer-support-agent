from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from backend.agent import process_ticket
from backend.database import get_ticket, initialize_database, insert_ticket, list_tickets, update_ticket_status
from backend.schemas import TicketCreate, TicketStatusUpdate

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(
    title="Intelligent Customer Support Agent API",
    description="Ticket classification, priority routing, response drafting, and human-review flags.",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "customer-support-agent"}


@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketCreate) -> dict:
    try:
        result = process_ticket(payload.subject, payload.description, payload.customer_email)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ticket processing failed: {type(exc).__name__}") from exc

    priority = result.get("priority", "Medium")
    ticket = {
        "id": str(uuid4()),
        "subject": payload.subject,
        "description": payload.description,
        "customer_email": payload.customer_email,
        "category": result.get("category", "Other"),
        "sentiment": result.get("sentiment", "Neutral"),
        "priority": priority,
        "needs_human_review": bool(result.get("needs_human_review", False)),
        "suggested_response": result.get("suggested_response", "A support representative will review your request."),
        "status": "In Review" if result.get("needs_human_review") else "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return insert_ticket(ticket)


@app.get("/tickets")
def get_tickets() -> list[dict]:
    return list_tickets()


@app.get("/tickets/{ticket_id}")
def get_ticket_by_id(ticket_id: str) -> dict:
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/tickets/{ticket_id}/status")
def change_ticket_status(ticket_id: str, payload: TicketStatusUpdate) -> dict:
    ticket = update_ticket_status(ticket_id, payload.status)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
