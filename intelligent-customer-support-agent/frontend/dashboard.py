from __future__ import annotations

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Support Operations Dashboard", page_icon="🎫", layout="wide")
st.title("🎫 Intelligent Customer Support")
st.caption("Submit support tickets, review AI classifications, and monitor escalations.")


def api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=90)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.subheader("Create a support ticket")
    with st.form("new_ticket", clear_on_submit=True):
        subject = st.text_input("Subject", placeholder="Order not delivered")
        email = st.text_input("Customer email", placeholder="customer@example.com")
        description = st.text_area(
            "Description",
            height=150,
            placeholder="Describe the issue and any action already taken...",
        )
        submitted = st.form_submit_button("Submit ticket", type="primary", use_container_width=True)

    if submitted:
        if not subject.strip() or not email.strip() or not description.strip():
            st.warning("Please complete all fields.")
        else:
            try:
                with st.spinner("The AI workflow is processing the ticket..."):
                    ticket = api_post(
                        "/tickets",
                        {"subject": subject, "customer_email": email, "description": description},
                    )
                st.success(f"Ticket created: {ticket['id'][:8]}")
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Could not contact the backend. Is FastAPI running? Details: {exc}")

st.subheader("Ticket overview")
try:
    tickets = api_get("/tickets")
    urgent = sum(ticket["priority"] == "Urgent" for ticket in tickets)
    high = sum(ticket["priority"] == "High" for ticket in tickets)
    pending = sum(ticket["needs_human_review"] for ticket in tickets)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total tickets", len(tickets))
    col2.metric("Urgent", urgent)
    col3.metric("High priority", high)
    col4.metric("Human review", pending)

    if not tickets:
        st.info("No tickets yet. Create one using the form in the sidebar.")
    else:
        st.dataframe(
            [
                {
                    "Ticket ID": ticket["id"][:8],
                    "Subject": ticket["subject"],
                    "Category": ticket["category"],
                    "Sentiment": ticket["sentiment"],
                    "Priority": ticket["priority"],
                    "Status": ticket["status"],
                    "Human review": "Required" if ticket["needs_human_review"] else "No",
                    "Created": ticket["created_at"],
                }
                for ticket in tickets
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Ticket details and suggested response")
        selection = st.selectbox(
            "Choose a ticket",
            options=tickets,
            format_func=lambda item: f"{item['id'][:8]} — {item['subject']}",
        )
        if selection:
            st.markdown(f"**Category:** {selection['category']}  |  **Sentiment:** {selection['sentiment']}  |  **Priority:** {selection['priority']}")
            st.markdown(f"**Customer:** {selection['customer_email']}")
            st.markdown("**Original description**")
            st.write(selection["description"])
            if selection["needs_human_review"]:
                st.warning("Human review required before responding or taking action.")
            st.markdown("**AI-generated response draft (not sent)**")
            st.write(selection["suggested_response"])
            new_status = st.selectbox(
                "Update status",
                ["Open", "In Review", "Resolved"],
                index=["Open", "In Review", "Resolved"].index(selection["status"]),
                key=f"status-{selection['id']}",
            )
            if st.button("Save status", key=f"save-{selection['id']}"):
                try:
                    response = requests.patch(
                        f"{API_BASE_URL}/tickets/{selection['id']}/status",
                        json={"status": new_status},
                        timeout=20,
                    )
                    response.raise_for_status()
                    st.success("Ticket status updated.")
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f"Status update failed: {exc}")
except requests.RequestException as exc:
    st.error(f"Backend unavailable at {API_BASE_URL}. Start FastAPI first. Details: {exc}")
