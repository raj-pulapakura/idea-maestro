## Idea Maestro – Product Vision

**One-liner:** Automatically bring your ideas to life with a group of specialized AI agents that critique, improve, and operationalize your project into a clear execution strategy.

### Problem

- **Idea paralysis**: People have ideas but struggle to refine them into something shippable.
- **Fragmented expertise**: You need business sense, marketing, technical execution, and critical feedback, which usually requires multiple experts.
- **LLM tools are passive**: Most tools just chat back; they don’t persist structured outputs or iterate on living documents.

### Solution

Idea Maestro is a **multi-agent system with a chat front-end** where:

- Users input:
  - Their **initial idea**
  - **Personal context** (bio, goals, constraints; optionally imported from LinkedIn, GitHub README, etc.)
- A group of **opinionated agents** (Devil’s Advocate, Angel Eyes, Capital Freak, Cake Man, Buzz, Mr. T) iteratively:
  - Ask clarifying questions
  - Propose changes
  - **Take action** by editing a set of **living documents** that represent the evolving idea.
- A central **Maestro/orchestrator** dynamically decides which agent should act next, based on:
  - What’s been covered so far
  - Current gaps (e.g., no monetization yet)
  - Conflicts between agents
  - New user input
- The user can **pause/resume** the loop, override agent edits, and steer the direction at any time.

At the end, the user has:

- A refined, realistic idea
- A clear execution strategy (technical + business + GTM)
- Exportable documents they can use to actually start building.

### Core Principles

- **Agents act, not just talk**:
  - Every agent turn is tied to concrete **document edits** (with diff previews), not just freeform advice.
- **User in the loop**:
  - Users can pause agents, answer questions, add their own edits, and resume the loop at any time.
- **Dynamic orchestration**:
  - No fixed “pipeline” of agents. The Maestro chooses which agent should respond next based on the evolving state.
- **Opinionated personas**:
  - Each agent has a clear ego/voice/values and occasionally disagrees with others, forcing tradeoffs into the open.
- **Pure credits monetization**:
  - The app runs on a **credits-based system** for simplicity. Users buy credits to power agent work; no BYOK in v1.

### Target Users

- Early-stage founders and indie hackers
- Builders with lots of ideas and limited time
- Non-technical founders who need structured help on tech + business + marketing
- Developers who want a sparring partner to pressure-test and scope ideas

### High-level User Journey

1. **Sign up** → Get onboarding and some free credits.
2. **Describe your idea** (short or long form) and optionally your background/goals.
3. **Watch the agents debate and refine**:
   - Devil’s Advocate attacks the idea.
   - Angel Eyes proposes fixes.
   - Capital Freak shapes the business model.
   - Cake Man pushes for 10x features.
   - Buzz designs GTM and distribution.
   - Mr. T scopes tech stack and milestones.
4. **Interact in the loop**:
   - Pause any time, respond, correct, or redirect.
   - See document diffs before/after each agent edit.
5. **Download your strategy**:
   - Pitch, roadmap, technical spec, GTM, risk register, etc.
6. **Return later** to iterate on the same idea or start a new one.


