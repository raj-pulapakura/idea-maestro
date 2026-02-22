# Idea Maestro

Idea Maestro is a multi-agent workspace for turning raw ideas into execution-ready plans.

You chat with a central orchestrator (`Maestro`), which routes work to specialized agents (Product Strategist, Growth Lead, Business Lead, and Technical Lead). Agents propose edits to a set of living planning documents, and you review and approve changes before they are applied.

## Key Features

- Multi-agent orchestration with role-specific specialist agents
- Thread-based workspaces for running multiple idea sessions
- Real-time streaming chat and agent/run status updates
- Living documents that evolve with each session (product, GTM, technical, business, risk, and action docs)
- Built-in review flow for staged edits (diffs + approve/reject/request changes)
- Run log and timeline view for visibility into agent and tool activity

## Tech Stack

- Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- Agent runtime: LangGraph + LangChain
- Models: OpenAI models (currently configured with GPT-family models)
- Database: PostgreSQL (via `psycopg`)
- Local/dev infrastructure: Docker + Docker Compose
