# 🤖 AI Customer Support Platform

<p align="center">
  <strong>Production-oriented AI customer support automation powered by LLMs, RAG, and agentic workflows.</strong>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.x-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI-LLM%20%7C%20RAG-8A2BE2" alt="AI">
  <img src="https://img.shields.io/badge/Architecture-Modular-blue" alt="Architecture">
  <img src="https://img.shields.io/badge/Status-In%20Development-orange" alt="Status">
</p>

---

## 🚀 Overview

The **AI Customer Support Platform** is a backend-first platform designed to automate customer support using modern AI technologies.

Instead of building a simple chatbot that only generates text, this project is designed around a complete support workflow:

```text
Customer
   │
   ▼
Support API
   │
   ▼
Intent Understanding
   │
   ▼
AI Support Agent
   │
   ├──────────────► Knowledge Base / RAG
   │
   ├──────────────► Business Tools
   │
   ├──────────────► Ticketing System
   │
   └──────────────► Human Escalation
   │
   ▼
Accurate Response
```

The long-term goal is to build a system that can **understand requests, retrieve trusted information, take appropriate actions, and escalate cases when AI should not handle them automatically.**

> 🚧 **Current status:** Early development. The **agentic support core** is implemented: a reason→act agent loop over the Anthropic Messages API, read-only business tools backed by SQLite, a ticketing system, and deterministic human-escalation backstops. RAG, auth, automation, and deployment are next.

---

# ✨ Features

## ✅ Currently Implemented

* FastAPI backend, modular package layout, OpenAPI / Swagger docs
* **Agentic support loop** — the agent reasons, calls tools, and answers, capped at `MAX_AGENT_STEPS` iterations
* **Business tools** (read-only, SQLite-backed): `lookup_customer`, `lookup_order`, `check_refund_eligibility`
* **Refund policy engine** — auto-approval only inside the return window, under an amount limit, delivered, not already refunded
* **Human-in-the-loop escalation** with three deterministic backstops:
  1. the model calls `escalate_to_human` (complaints, security, low confidence)
  2. the model calls a **sensitive** tool (`issue_refund`) — intercepted, never executed by the AI, turned into a ticket
  3. the loop exceeds its step budget
* **Ticketing system** — every escalation opens a ticket with a transcript snapshot; full CRUD API
* **Pluggable LLM seam** — the agent depends on a small protocol, so the loop is unit-tested with a scripted client and zero network calls
* Seeded demo data (customers + orders) and a 25-test suite

### API

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET`  | `/health` | Liveness check |
| `POST` | `/chat` | Run the support agent on one customer message |
| `GET`  | `/tickets` | List tickets (optional `?status=`) |
| `POST` | `/tickets` | Open a ticket manually |
| `GET`  | `/tickets/{id}` | Fetch one ticket |
| `PATCH`| `/tickets/{id}` | Update ticket status |

`POST /chat` requires `ANTHROPIC_API_KEY`; without it the endpoint returns `503` and the tools/tickets APIs still work.

Example — `POST /chat`:

```json
{ "message": "Where is my order ORD-1002?", "customer_email": "ada@example.com" }
```

```json
{
  "conversation_id": "9f2c...",
  "reply": "Your USB-C hub (ORD-1002) shipped 3 days ago and is on its way.",
  "resolved": true,
  "escalated": false,
  "ticket_id": null,
  "steps": 2,
  "tool_calls": [
    { "step": 1, "name": "lookup_order", "input": { "order_id": "ORD-1002" }, "outcome": "{\"found\": true, ...}" }
  ]
}
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 🔮 Planned AI Capabilities

### 🧠 Intelligent Support Agent

The platform will be capable of:

* Understanding customer intent
* Maintaining conversation context
* Generating contextual responses
* Deciding when tools are required
* Handling multi-step support workflows

### 📚 RAG Knowledge Base

The knowledge system will allow businesses to connect internal information such as:

* Product documentation
* FAQs
* Policies
* Help-center articles
* Manuals
* Internal documentation

The AI can then retrieve relevant information before generating an answer.

### 🛠️ AI Tools

Future tools may include:

```text
Customer Lookup
      ↓
Order Lookup
      ↓
Refund / Return Check
      ↓
Ticket Creation
      ↓
Account Information
      ↓
Human Escalation
```

This moves the system beyond **"chat"** toward **action-oriented AI support**.

---

# 🏗️ Architecture

The platform is being designed as a modular system so individual components can evolve independently.

```text
                         ┌─────────────────────┐
                         │      Customer       │
                         │ Web / App / Chat    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │     API Gateway     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Support Orchestrator   │
                    │                              │
                    │   Intent → Reason → Act      │
                    └──────────────┬───────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
      ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
      │     LLM      │     │   RAG / KB   │     │ AI Tools     │
      │              │     │              │     │              │
      │ Reasoning    │     │ Company Docs │     │ CRM / Orders │
      │ Generation   │     │ Retrieval    │     │ Tickets      │
      └──────────────┘     └──────────────┘     └──────┬───────┘
                                                       │
                                                       ▼
                                             ┌─────────────────┐
                                             │ Human Support   │
                                             │   Escalation    │
                                             └─────────────────┘
```

### Core design principles

* **Modular architecture**
* **API-first development**
* **Separation of concerns**
* **Retrieval-grounded responses**
* **Tool-based actions**
* **Human-in-the-loop escalation**
* **Testability**
* **Production readiness**

---

# 💼 Why Companies Would Use This

Customer support teams repeatedly handle the same categories of questions:

> "Where is my order?"

> "How do I reset my password?"

> "Can I get a refund?"

> "What is your pricing?"

> "How does this feature work?"

A traditional support workflow often requires a human agent to manually search documentation, inspect customer information, and respond.

This platform aims to automate that workflow.

### Without AI automation

```text
Customer
   ↓
Support Agent
   ↓
Search Documentation
   ↓
Check Customer Information
   ↓
Write Response
   ↓
Customer
```

### With an AI support platform

```text
Customer
   ↓
AI Support Agent
   ↓
Retrieve Knowledge
   ↓
Use Business Tools
   ↓
Generate Response
   ↓
Resolve
   │
   └──► Escalate to Human when necessary
```

### Potential business benefits

| Challenge                | Platform Approach       |
| ------------------------ | ----------------------- |
| Repetitive questions     | AI automation           |
| Slow response times      | Automated responses     |
| Large documentation sets | RAG knowledge retrieval |
| Support agent workload   | AI-assisted resolution  |
| Inconsistent answers     | Grounded knowledge      |
| Complex requests         | Tool-enabled agents     |
| Sensitive/complex cases  | Human escalation        |
| Multiple systems         | API/tool integrations   |

The goal is **not to replace human support completely**.

The goal is to allow human support teams to spend more time on difficult problems while AI handles repetitive, well-defined workflows.

---

# 🎬 Demo

## Current API Demo

Start the development server:

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

You will see the automatically generated Swagger UI.

### Health Check

```http
GET /health
```

Expected:

```json
{
  "status": "healthy"
}
```

---

## 📸 Screenshots

Screenshots will be added as the platform develops.

Planned demonstrations include:

### Swagger API

```text
screenshots/
└── swagger-api.png
```

### AI Support Conversation

```text
screenshots/
└── ai-support-demo.png
```

### RAG Knowledge Retrieval

```text
screenshots/
└── rag-demo.png
```

### Ticket Escalation

```text
screenshots/
└── human-escalation.png
```

> Real screenshots will be added once these features are implemented. No mock screenshots are used in this repository.

---

# 🛠️ Tech Stack

| Technology       | Role                         |
| ---------------- | ---------------------------- |
| 🐍 Python        | Core backend                 |
| ⚡ FastAPI        | REST API                     |
| 🤖 LLMs          | AI reasoning and generation  |
| 📚 RAG           | Knowledge-grounded responses |
| 🔎 Vector Search | Semantic retrieval           |
| 🗄️ PostgreSQL   | Application data             |
| 🐳 Docker        | Containerization             |
| 🧪 Pytest        | Testing                      |
| 🔄 n8n           | Workflow automation          |
| 🔐 JWT / OAuth   | Authentication               |
| 📊 Observability | Monitoring and debugging     |

Technologies marked as planned will be integrated as development progresses.

---

# 📁 Project Structure

```text
ai-customer-support-platform/
│
├── src/
│   ├── api/
│   │   ├── main.py            # FastAPI app + lifespan (init DB, seed)
│   │   ├── deps.py            # settings / DB / LLM / conversation-store providers
│   │   └── routes/            # health, chat, tickets
│   │
│   ├── agent/
│   │   ├── orchestrator.py    # the reason→act loop + escalation backstops
│   │   ├── tools.py           # tool schemas + dispatcher
│   │   ├── llm.py             # LLMClient protocol, Anthropic + scripted clients
│   │   └── prompts.py         # support system prompt
│   │
│   ├── services/
│   │   ├── business.py        # lookup_customer / lookup_order / refund policy
│   │   └── tickets.py         # ticket persistence
│   │
│   ├── core/
│   │   ├── config.py          # pydantic-settings
│   │   └── db.py              # SQLite connection + schema
│   │
│   ├── models/schemas.py      # API request/response models
│   └── data/seed.py           # demo customers + orders
│
├── tests/                     # 25 tests, no network (scripted LLM)
│
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
└── ...
```

The structure will expand as new modules are introduced.

---

# ⚙️ Getting Started

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai-customer-support-platform
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -e ".[dev]"
```

## 4. Configure the environment

```bash
cp .env.example .env
# then set ANTHROPIC_API_KEY in .env to enable POST /chat
```

## 5. Run the API

```bash
uvicorn api.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

# 🧪 Testing

Automated tests will be added alongside each major component.

Run:

```bash
pytest
```

The project follows a test-as-you-build approach so new functionality is verified before being integrated into the main system.

---

# 🗺️ Roadmap

```text
                         ┌──────────────────┐
                         │  API Foundation  │
                         │       ✅         │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Support Backend  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   LLM Support    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   RAG / Search   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Agentic Tools   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Human Escalation │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Automation     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Docker / CI / CD │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Production    │
                         └──────────────────┘
```

### Development phases

* [x] Project foundation
* [x] FastAPI application
* [x] Health endpoint
* [x] OpenAPI documentation
* [x] Configuration system (`pydantic-settings`)
* [x] Database integration (SQLite)
* [x] Ticket management (models + CRUD API)
* [x] LLM integration (Anthropic Messages API, pluggable client)
* [x] AI support agent (reason→act loop)
* [x] Agent tools (customer / order / refund lookups)
* [x] Human escalation (model-driven + deterministic backstops)
* [ ] Conversation persistence (currently in-process only)
* [ ] RAG pipeline
* [ ] Knowledge-base management
* [ ] Authentication & authorization
* [ ] Workflow automation
* [ ] Docker
* [ ] CI/CD
* [ ] Monitoring
* [ ] Production deployment

---

# 🔐 Security

Security will be treated as a first-class component.

Planned capabilities include:

* Authentication and authorization
* Role-based access control
* Input validation
* Rate limiting
* Secure secret management
* Audit logging
* Protected AI tools
* Customer-data protection
* Human approval for sensitive actions

**Never commit API keys, passwords, tokens, or production credentials to this repository.**

---

# 🧠 Engineering Goals

This project is being built to demonstrate practical AI engineering rather than simply calling an LLM API.

Key engineering goals:

```text
Reliable AI
     +
Grounded Knowledge
     +
Tool Calling
     +
Backend Engineering
     +
Automation
     +
Security
     +
Testing
     +
Observability
     =
Production-Ready AI Support Platform
```

---

# 🤝 Contributing

Contributions, ideas, issues, and improvements are welcome.

For major changes, please open an issue first to discuss the proposed change.

---

# 📄 License

This project is currently under active development.

A production license will be added before public deployment.

---

# 👨‍💻 Author

## Zeeshan Qadir

AI / Software Engineering focused on:

* Artificial Intelligence
* AI Agents
* Retrieval-Augmented Generation
* LLM Applications
* Backend Engineering
* Automation
* Production AI Systems

---

<p align="center">
  <strong>Building AI systems that don't just answer — they understand, retrieve, act, and escalate.</strong>
</p>
