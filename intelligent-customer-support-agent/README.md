# Intelligent Customer Support Agent

A small AI-assisted ticketing application that classifies customer complaints, estimates priority, drafts a suggested response, and flags high-risk tickets for human review. A LangGraph workflow orchestrates the steps, FastAPI exposes REST endpoints, SQLite stores tickets, and Streamlit provides a lightweight operations dashboard.

> **Portfolio note:** This is an original starter implementation. Run it, test the workflows, customize the categories or escalation rules, and understand how human approval works before presenting it as a completed project.

## Features

- Submit customer support tickets through a web dashboard or REST API.
- Use an LLM to classify complaints and identify sentiment.
- Apply deterministic priority rules for consistent escalation.
- Orchestrate processing with a LangGraph state graph.
- Generate a suggested response without sending it automatically.
- Flag urgent/high-priority tickets for human review.
- Persist tickets in SQLite.
- View tickets through a Streamlit dashboard.
- Expose interactive API documentation through FastAPI.

## Architecture

`Streamlit UI -> FastAPI -> LangGraph workflow -> Groq LLM + priority rules -> SQLite`

High-priority tickets are flagged for human review. The application does **not** send customer emails or perform refunds automatically.

## Requirements

- Python 3.10 or newer
- A Groq API key: https://console.groq.com/keys

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and enter your Groq key:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Never commit `.env` or publish your API key.

### 4. Start the backend

Run from the project root:

```bash
uvicorn backend.app:app --reload
```

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 5. Start the dashboard

Open a second terminal in the same project folder, activate the same virtual environment, and run:

```bash
streamlit run frontend/dashboard.py
```

Open the local URL printed by Streamlit, usually http://localhost:8501.

## Run tests

```bash
pytest -q
```

## Example ticket

**Subject:** Order not delivered

**Description:** My order was due yesterday and has not arrived. I have contacted support twice and need an update.

Expected workflow: classify the ticket, estimate sentiment and priority, draft a response, and flag the ticket for human review if the rules indicate high priority.

## Responsible AI and limitations

- AI-generated classifications and suggested responses can be wrong; a human should review important decisions.
- The app never sends an email or performs a refund automatically.
- Priority rules are illustrative and should be reviewed before use in a real support operation.
- The starter uses local SQLite and is intended for a portfolio/demo, not production multi-user deployment.
- Do not submit real customer personal data to an external LLM without authorization and appropriate safeguards.

## Suggested extensions

1. Add role-based authentication for support agents.
2. Add a knowledge-base RAG tool for policy-grounded responses.
3. Add response-time and resolution-rate analytics.
4. Add audit logs and human approval endpoints.
5. Add Docker and a CI workflow for tests.

## Technology stack

Python, LangGraph, Groq API, FastAPI, SQLite, Streamlit, Pydantic, pytest.
