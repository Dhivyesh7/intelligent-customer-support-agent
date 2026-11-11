from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import END, START, StateGraph

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class TicketState(TypedDict, total=False):
    subject: str
    description: str
    customer_email: str
    category: str
    sentiment: str
    priority: str
    needs_human_review: bool
    suggested_response: str


def _client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Copy .env.example to .env and add your key.")
    return Groq(api_key=api_key)


def classify_ticket(state: TicketState) -> dict:
    """Use the LLM to classify a ticket. Fall back safely if JSON parsing fails."""
    prompt = (
        "Classify this customer support ticket. Return ONLY valid JSON with exactly these keys: "
        '"category" (one of Delivery, Payment, Refund, Account, Technical, Other), '
        '"sentiment" (one of Positive, Neutral, Negative, Angry). '
        "Do not include markdown.\n\n"
        f"Subject: {state.get('subject', '')}\nDescription: {state.get('description', '')}"
    )
    try:
        completion = _client().chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You classify support tickets conservatively."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = completion.choices[0].message.content or "{}"
        data = json.loads(raw)
        categories = {"Delivery", "Payment", "Refund", "Account", "Technical", "Other"}
        sentiments = {"Positive", "Neutral", "Negative", "Angry"}
        category = data.get("category", "Other")
        sentiment = data.get("sentiment", "Neutral")
        if category not in categories:
            category = "Other"
        if sentiment not in sentiments:
            sentiment = "Neutral"
        return {"category": category, "sentiment": sentiment}
    except Exception:
        # A safe fallback keeps the workflow explainable if the model returns invalid output.
        text = f"{state.get('subject', '')} {state.get('description', '')}".lower()
        if any(word in text for word in ("refund", "money back", "reimburse")):
            category = "Refund"
        elif any(word in text for word in ("payment", "charged", "bill", "invoice")):
            category = "Payment"
        elif any(word in text for word in ("delivery", "delivered", "shipment", "order")):
            category = "Delivery"
        elif any(word in text for word in ("login", "password", "account")):
            category = "Account"
        elif any(word in text for word in ("error", "bug", "technical", "app crash")):
            category = "Technical"
        else:
            category = "Other"
        sentiment = "Angry" if any(w in text for w in ("angry", "furious", "unacceptable")) else "Neutral"
        return {"category": category, "sentiment": sentiment}


def assign_priority(state: TicketState) -> dict:
    """Apply deterministic safety and urgency rules after LLM classification."""
    text = f"{state.get('subject', '')} {state.get('description', '')}".lower()
    critical_terms = ("injury", "unsafe", "safety", "fraud", "hacked", "security breach")
    urgent_terms = ("urgent", "immediately", "asap", "not delivered", "charged twice")

    if any(term in text for term in critical_terms):
        priority = "Urgent"
    elif state.get("sentiment") == "Angry" or any(term in text for term in urgent_terms):
        priority = "High"
    elif state.get("sentiment") == "Negative":
        priority = "Medium"
    else:
        priority = "Low"
    return {"priority": priority}


def needs_review(state: TicketState) -> str:
    return "human_review" if state.get("priority") in {"Urgent", "High"} else "draft_response"


def mark_for_human_review(state: TicketState) -> dict:
    return {"needs_human_review": True}


def draft_response(state: TicketState) -> dict:
    prompt = (
        "Write a concise, empathetic customer-support draft response. Do not claim that an action "
        "has already been completed. Do not promise refunds, delivery dates, or policy exceptions. "
        "State that a support representative will verify the details where needed.\n\n"
        f"Category: {state.get('category')}\nPriority: {state.get('priority')}\n"
        f"Subject: {state.get('subject')}\nDescription: {state.get('description')}"
    )
    try:
        completion = _client().chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You draft safe and professional customer-support replies."},
                {"role": "user", "content": prompt},
            ],
        )
        response = completion.choices[0].message.content or "A support representative will review your request."
    except Exception as exc:
        response = (
            "Thank you for contacting support. We have recorded your request and a representative "
            f"will review it. (Draft fallback: {type(exc).__name__})"
        )
    return {"suggested_response": response}


def build_workflow():
    graph = StateGraph(TicketState)
    graph.add_node("classify", classify_ticket)
    graph.add_node("prioritize", assign_priority)
    graph.add_node("human_review", mark_for_human_review)
    graph.add_node("draft_response", draft_response)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "prioritize")
    graph.add_conditional_edges(
        "prioritize",
        needs_review,
        {"human_review": "human_review", "draft_response": "draft_response"},
    )
    graph.add_edge("human_review", "draft_response")
    graph.add_edge("draft_response", END)
    return graph.compile()


workflow = build_workflow()


def process_ticket(subject: str, description: str, customer_email: str) -> dict:
    result = workflow.invoke(
        {"subject": subject, "description": description, "customer_email": customer_email}
    )
    return result
