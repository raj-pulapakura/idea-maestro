## Architecture and Tech Stack

### High-level Architecture

```
User
  ↓
Next.js Frontend
  - Chat UI
  - Docs viewer/editor
  - Auth & credits UI
  ↓
FastAPI Backend (Python API)
  - Maestro orchestrator
  - Agent runners
  - Credit metering
  - Persistence API
  ↓
Postgres (Railway)
  - Users, sessions, messages
  - Documents & versions
  - Credits and transactions
  ↓
LLM Provider(s) (your keys, NOT BYOK in v1)
  - OpenAI / Anthropic / etc.
```

### Frontend

- **Framework**: Next.js (App Router)
- **Hosting**: Railway (Node service) or another Node-friendly host
- **Styling**: Tailwind CSS or similar utility-first CSS
- **Key Responsibilities**:
  - Render the multi-agent chat interface.
  - Show and edit living documents.
  - Manage auth, sign-up, and login.
  - Display credits balance, purchase flows, and usage warnings.
  - Call backend API for:
    - Sending messages.
    - Triggering agent loops.
    - Buying credits.

### Backend

- **Runtime**: Python + FastAPI, deployed as a long-running service on Railway.
- **Core services**:
  - **Maestro/orchestration**:
    - Reads session state (messages, docs, open questions).
    - Decides which agent should act next.
    - Invokes a single “agent runner” with the appropriate prompt and context.
  - **Agent runner**:
    - Wraps the LLM call.
    - Injects persona, ego, and task instructions.
    - Produces both:
      - Natural language explanation for the chat.
      - Structured document edits (patches/diffs).
  - **Document manager**:
    - Applies patches to the right document(s).
    - Tracks versions and history.
    - Supports rollbacks.
  - **Credits system**:
    - Checks and decrements credits for each operation.
    - Records usage in a transaction log.
  - **Payments webhooks**:
    - Listens to Stripe events (payment succeeded, refunds, etc.).
    - Updates user credit balances and subscription state.

### Persistence (Postgres on Railway)

Key tables (conceptual):

- `users` – user profile + auth linkage.
- `api_sessions` – login sessions (if needed beyond Supabase built-ins).
- `chat_sessions` – one row per idea refinement session.
- `messages` – full chat history, including:
  - user messages
  - agent messages
  - system/orchestrator messages
- `documents` – current snapshots of living documents.
- `document_versions` – historical versions for diffing/rollback.
- `user_tiers` – credit balance and (future) subscription status.
- `credit_transactions` – immutable ledger of credit usage/purchases.

### LLM Integration

- **v1 simplification**:
  - Use a **single primary provider** (e.g., OpenAI).
  - Use 1–2 models (e.g., GPT-4 for complex, GPT-4-mini or 3.5 for cheaper tasks).
  - Route all agents through a simple “callLLM” service.

### Streaming

- Use **streaming responses** so the user sees agent thinking in real time:
  - Backend: stream tokens from the LLM through a FastAPI endpoint (e.g., using Server-Sent Events or chunked responses).
  - Frontend: consume the stream (e.g., via `fetch` with streams or WebSockets) and progressively render messages.
  - Once complete, apply the associated document edits on the client.

### Low-cost Deployment

- **Railway**:
  - Host the Next.js frontend and the FastAPI backend as separate services.
  - Provide a managed Postgres instance for persistence.
- **Stripe**:
  - No monthly cost; pay per transaction.
- **LLMs**:
  - You pay per token, built into your credit pricing.


