## Agents, Personas, and UX

### Agent Roster

- **Product Strategist**  
  - Role: Product strategy lead focused on problem framing, ICP, and prioritization.  
  - Values: Clarity over fluff, user outcomes over feature sprawl.  
  - Typical actions:
    - Improves **Product Brief** clarity and differentiation.
    - Tightens **MVP Scope & Non-Goals**.
    - Captures key product tradeoffs in **Risk & Decision Log**.

- **Growth Lead**  
  - Role: Messaging, distribution, and experiment planning specialist.  
  - Values: Discoverability, crisp positioning, test-and-learn execution.  
  - Typical actions:
    - Defines launch sequence and channel strategy in **GTM Plan**.
    - Sharpens ICP/messaging in **Product Brief**.
    - Adds near-term growth experiments to **Next Actions Board**.

- **Business Lead**  
  - Role: Business model and economic viability owner.  
  - Values: Sustainable unit economics and explicit assumptions.  
  - Typical actions:
    - Maintains **Business Model & Pricing** decisions.
    - Tracks confidence-tagged assumptions in **Evidence & Assumptions Log**.
    - Documents financial tradeoffs in **Risk & Decision Log**.

- **Technical Lead**  
  - Role: Technical execution and delivery risk owner.  
  - Values: Practical architecture, speed-to-ship, controlled complexity.  
  - Typical actions:
    - Maintains **Technical Plan** with milestones and dependencies.
    - Enforces clear MVP cut lines via **MVP Scope & Non-Goals**.
    - Adds delivery-critical tasks to **Next Actions Board**.

### Living Documents

These are the shared artifacts agents continuously edit:

- **Product Brief** – Problem, ICP, value proposition, and positioning.
- **Evidence & Assumptions Log** – Assumptions with confidence and validation status.
- **MVP Scope & Non-Goals** – What is in MVP vs explicitly out of scope.
- **Technical Plan** – Architecture, stack, milestones, constraints.
- **GTM Plan** – Launch sequence, channels, and growth experiments.
- **Business Model & Pricing** – Monetization, packaging, pricing, and economics.
- **Risk & Decision Log** – Major risks, decisions, and rationale.
- **Next Actions Board** – Prioritized tasks for the next two weeks.

Each agent’s turn typically:

- Explains *why* they’re making changes.
- Applies concrete edits to one or more documents.
- Shows a **diff-style preview** before/after.
- Optionally asks clarifying questions.

### UX Concepts

#### Dual-pane Layout

- **Left: Chat Panel**
  - Messages from agents and user.
  - Agent avatars, colors, and names.
  - Inline tags (e.g., “edited: Risk & Decision Log, Product Brief”).
  - “Pause loop” and “Resume” controls.

- **Right: Documents Panel**
  - List of all living documents with status (e.g., “Product Brief: v7, updated 2m ago by Product Strategist”).
  - Clicking opens full doc view and history.
  - Optional diff view tied to a specific agent message.

#### User-in-the-Loop Controls

- **Pause / Resume**  
  - At any point, user can pause agent loop.
  - While paused, user can:
    - Reply to agents.
    - Edit documents directly.
    - Answer open questions.

- **Diff Approval (optional for later)**  
  - Agents propose edits as patches.
  - User can accept/reject individual diffs before they are committed.

- **Clarifying Questions Queue**
  - Agents add questions to a visible list (with who asked + context).
  - Some questions can be marked as “blocking” for certain docs.
  - The Maestro can pause or avoid synthesizing final output until key questions are answered.

### Maestro (Orchestrator) Behavior

High-level logic:

- If user just spoke:
  - Route to the **agent most relevant** to what user said.
  - If user answered a specific question, give turn to the agent who asked it.
- If there are **blocking questions** unanswered:
  - Prefer to pause or nudge the user before continuing deeper.
- If a document was just heavily edited by one agent:
  - Consider giving the next turn to a complementary agent (e.g., after Growth Lead proposes aggressive experiments, let Business Lead validate economics).
- If major areas (risk, monetization, GTM, tech, roadmap) aren’t covered yet:
  - Pick agents whose domains are underrepresented.
- If everything is reasonably covered and no blocking questions remain:
  - Switch into **synthesis mode** to finalize docs.
