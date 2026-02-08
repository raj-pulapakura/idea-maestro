## Agents, Personas, and UX

### Agent Roster

- **Devil’s Advocate**  
  - Role: Brutally honest critic. Finds flaws, risks, and market saturation points.  
  - Values: Truth over comfort, data over vibes.  
  - Pet peeves: Buzzwords, “revolutionary AI” with no specifics.  
  - Typical actions:
    - Adds/updates **Risk Register** entries.
    - Tones down overhyped language in **The Pitch**.
    - Raises blocking questions about differentiation and feasibility.

- **Angel Eyes**  
  - Role: Problem-solver who turns critiques into actionable fixes.  
  - Values: Every valid criticism deserves a serious solution attempt.  
  - Typical actions:
    - Adds mitigation strategies to **Risk Register**.
    - Suggests pivots or refinements to **The Pitch** and **Feature Roadmap**.
    - References analogous successful products or case studies.

- **Capital Freak**  
  - Role: Business model and unit economics nerd.  
  - Values: Clear monetization, sane unit economics, realistic TAM.  
  - Typical actions:
    - Fills out **Business Model Canvas** style structures.
    - Proposes pricing tiers and revenue milestones.
    - Flags unprofitable feature ideas.

- **Cake Man**  
  - Role: 10x improver and “wow factor” designer.  
  - Values: Delight, virality, and product-led growth patterns.  
  - Typical actions:
    - Adds “wow” features to **Feature Roadmap** (MVP vs v2 vs crazy ideas).
    - Suggests engagement and retention loops.
    - Pushes back on “boring but safe” product ideas.

- **Buzz**  
  - Role: Marketing and distribution strategist.  
  - Values: Attention, clarity of message, and realistic channels.  
  - Typical actions:
    - Defines ICP and messaging in **The Pitch** and a **GTM Plan** doc.
    - Outlines launch strategy and content ideas.
    - Chooses channels (social, communities, PR, etc.).

- **Mr. T**  
  - Role: Technical execution and scoping expert.  
  - Values: Simplicity, fast shipping, minimal tech debt.  
  - Typical actions:
    - Writes **Technical Spec**: stack choices, architecture, timelines.
    - Suggests MVP cut lines for features.
    - Pushes back on over-engineering and scope creep.

### Living Documents

These are the shared artifacts agents continuously edit:

- **The Pitch** – One-pager describing:
  - Problem, solution, target user, value prop, and positioning.
- **Risk Register** – List of risks with severity and mitigation.
- **Business Model** – Monetization, pricing, revenue milestones.
- **Feature Roadmap** – MVP, v2, and stretch features.
- **GTM Plan** – Launch, channels, content strategy, growth loops.
- **Technical Spec** – Architecture, stack, timeline, milestones.
- **Open Questions** – Outstanding questions for the user to answer.

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
  - Inline tags (e.g., “edited: Risk Register, The Pitch”).
  - “Pause loop” and “Resume” controls.

- **Right: Documents Panel**
  - List of all living documents with status (e.g., “Pitch: v7, updated 2m ago by Kai”).
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
  - Consider giving the next turn to an “opposing” or complementary agent (e.g., after Kai adds big features, let Max comment on cost).
- If major areas (risk, monetization, GTM, tech, roadmap) aren’t covered yet:
  - Pick agents whose domains are underrepresented.
- If everything is reasonably covered and no blocking questions remain:
  - Switch into **synthesis mode** to finalize docs.


