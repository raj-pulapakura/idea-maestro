## Idea Maestro – Frontend UI Design Spec

### 1. Overall Layout

- **Viewport layout**
  - 3-column desktop layout:
    - **Left Column: Chat History Panel** (fixed width, ~260–320px)
    - **Center Column: Main Chat Panel** (flex / fluid, primary focus)
    - **Right Column: Documents Panel** (fixed width, ~360–420px)
  - Sticky **top app bar** spanning all three columns:
    - App name + logo.
    - Current workspace / project name.
    - Global controls: **Pause / Resume**, synthesis-mode indicator, Settings.
  - Light theme optimized for readability and diff visualization.

---

### 2. Main Chat Panel (Center)

#### 2.1 Structure

- **Header (center column)**
  - Title: **“Agent Workspace”** or current idea name.
  - Subheader: summary line, e.g. “5 agents active · Pitch v7 · Last update 2m ago”.
  - Optional filters: dropdowns for **Agent**, **Document**, **Activity Type** (chat, diff, approval).

- **Message list**
  - Scrollable vertical list of chat messages.
  - Each message includes:
    - **Agent avatar + name + role**, e.g. “Devil’s Advocate – Brutal critic”.
    - Timestamp.
    - Inline **activity tags**, aligned with `docs/02-agents-and-ux.md`:
      - “edited: Risk Register, The Pitch”.
      - “asked: 2 questions (1 blocking)”.
      - “proposed: 3 diffs (awaiting approval)”.
  - Consecutive messages from the same agent are visually grouped (subtle connector, reduced repeated header).

- **Message types**
  - **Standard text message**
    - Rich text (headings, bullets, inline code, links).
  - **Diff proposal message**
    - Includes one or more **diff preview cards** (see section 4.2).
  - **Approval / review message**
    - Displays decision state (Approved / Rejected / Needs Changes) with icon + color.
  - **Clarifying question message**
    - List of questions, each labeled as **Blocking** or **Non-blocking** and linked to specific docs.

#### 2.2 Composer Area

- **Input**
  - Multi-line text area.
  - Supports:
    - **Agent @mentions**:
      - Typing `@` opens a dropdown with:
        - Avatar.
        - Name.
        - Role summary (from `docs/02-agents-and-ux.md`):
          - Devil’s Advocate – risks & critique.
          - Angel Eyes – solutions.
          - Capital Freak – business model.
          - Cake Man – wow-factor.
          - Buzz – GTM.
          - Mr. T – technical scope.
          - Maestro – orchestrator.
      - Selected mention renders as a colored pill, e.g. `@Devil’s Advocate`.
    - **Document #mentions**:
      - Typing `#` shows living docs:
        - The Pitch.
        - Risk Register.
        - Business Model.
        - Feature Roadmap.
        - GTM Plan.
        - Technical Spec.
        - Open Questions.
      - Selected doc renders as a pill, e.g. `#Risk Register`.
  - Optional quick action chips above the input:
    - “Ask a blocking question”.
    - “Request critique from Devil’s Advocate”.
    - “Request tech scope from Mr. T”.

- **Actions**
  - Primary button: **Send**.
  - Secondary split-button / dropdown:
    - “Send & propose diffs”.
    - “Send as note (no agent action)”.
  - Status hint text: “@mention agents and #mention docs to guide the Maestro.”

---

### 3. Left Panel – Chat History & Sessions

#### 3.1 Purpose

- Persistent navigation for **sessions / workspaces**.
- Provide overview of which agents and documents are active in each session.

#### 3.2 Content

- **Top bar (left panel)**
  - Title: **“Sessions”**.
  - Search input: “Search chats, agents, docs”.
  - Button: **New Session**.

- **Session list**
  - Each item shows:
    - Session title (e.g. “Solo Founder AI PM”, “Idea Maestro Onboarding”).
    - Subtext:
      - Recent agents and docs: “Devil’s Advocate, Mr. T · Pitch, Risk Register”.
    - Badges:
      - Status: “Live”, “Paused”, or “Completed”.
      - Indicator for **blocking questions**: small red “Blocking questions” chip.
  - On select:
    - Loads session chat into **Main Chat Panel**.
    - Filters **Documents Panel** to docs relevant to that session.

- **Filters**
  - Chips above list:
    - All / Active / Paused / Completed.
    - Toggle “Has blocking questions”.

---

### 4. Right Panel – Documents & Diffs

#### 4.1 Documents List View

- **Header (right panel)**
  - Title: **“Living Documents”**.
  - “+ New from Template” button:
    - Dropdown: Pitch, Risk Register, Business Model, Feature Roadmap, GTM Plan, Technical Spec, Open Questions.
  - Filter by:
    - Document type.
    - Last edited by agent.

- **Document items**
  - For each doc:
    - Title: e.g. “The Pitch”.
    - Status line:
      - Version + recency + last editor:
      - “v7 · updated 2m ago by Angel Eyes”.
    - Badges:
      - “Draft”, “Stable”, “Needs review”.
      - “Has blocking question”.
    - Actions:
      - “Open”.
      - “History”.

- **On click – Document detail view**
  - Right panel switches to document detail with tabs:
    - **Current** – read-only or editable view of latest content.
    - **History** – version list with timestamps, agent, and high-level summaries.
    - **Diffs** – focused diff proposals related to this doc.
  - “Current” tab:
    - Typography optimized for long-form reading.
    - Optional inline comment anchors.

#### 4.2 Diff View & Approvals

- **Diff mode activation**
  - Triggered by:
    - Clicking an “edited: [doc]” tag in a chat message.
    - Clicking “View diffs” from document detail.

- **Diff presentation**
  - Two layout options (configurable):
    - Side-by-side: **Before** (left) vs **After** (right).
    - Inline: single column with additions/deletions highlighted.
  - Each diff has:
    - Title/summary line:
      - “Capital Freak tightened pricing tiers.”
    - Metadata:
      - Proposed by [Agent], time, related session.
    - Focus on **changed sections only**, with context lines.

- **Approval controls (detailed)**
  - Buttons:
    - **Approve**.
    - **Reject**.
    - **Request changes**.
  - Checkbox: “Apply all diffs from this agent message”.
  - After action:
    - Status pill: e.g. “Approved by you · 1:07 PM”.
    - Option: “Approve & notify agent” which posts a summarized review message into chat.

- **Diff queue**
  - Collapsible list in right panel:
    - Each card shows doc name, agent, short summary, and status:
      - Pending / Approved / Rejected.
    - Clicking card focuses that diff in the main diff view.

---

### 5. Approval & Review UX (Cross-Cutting)

#### 5.1 Inline Approval in Chat

- For each diff proposal message:
  - Embedded **approval widget** below the text content:
    - Summary: “3 changes to Risk Register (risk severity updates)”.
    - Buttons:
      - “Quick Approve”.
      - “Quick Reject”.
      - “View details” (opens right panel diff mode).
  - Widget reflects state after action:
    - Icon + label, e.g. “Approved · v5 → v6”.

#### 5.2 Review History

- In each document’s **History** tab:
  - Timeline of changes:
    - “v6 → v7 · Approved by User · Proposed by Cake Man · 3 diffs merged.”
  - Filters:
    - Approved / Rejected / Pending proposals.
  - Clicking a history item:
    - Opens read-only diff view for that version jump.

---

### 6. Agent @Mention UX

#### 6.1 Trigger and Dropdown

- Typing `@` in the composer:
  - Opens dropdown anchored to caret.
  - List items show:
    - Avatar.
    - Name.
    - Role (from `docs/02-agents-and-ux.md`), e.g.:
      - Devil’s Advocate – brutally honest critic, finds risks.
      - Angel Eyes – turns critiques into actionable fixes.
      - Capital Freak – business model & unit economics.
      - Cake Man – wow factor & virality.
      - Buzz – marketing & distribution.
      - Mr. T – technical spec & scoping.
  - Keyboard navigation (↑/↓, Enter) and mouse selection.

#### 6.2 Rendering & Semantics

- After selection:
  - Mention becomes a colored pill: `@Angel Eyes`.
  - Hover tooltip:
    - Short role description + examples of typical actions.
  - Multiple mentions allowed:
    - E.g. “@Devil’s Advocate and @Angel Eyes please refine the #Risk Register mitigation plan.”

- Post-send indicators:
  - On the message bubble:
    - “Routed to: Devil’s Advocate” or “Routed to: Maestro (auto)”.
  - If no explicit @mention:
    - Show subtle label: “Auto-routed to [Agent] by Maestro”.

---

### 7. User-in-the-Loop Controls

#### 7.1 Pause / Resume Agent Loop

- **Global control in top app bar**:
  - When running:
    - Button label: **Pause agents**.
  - When paused:
    - Button label: **Resume agents**.
    - App-wide banner at top of main chat:
      - Text: “Agents are paused. You can reply, edit docs, and answer questions; they will not auto-respond until you resume.”

- **Paused state behavior**
  - Agents stop posting new messages automatically.
  - Main chat shows:
    - Call-to-action buttons:
      - “Review pending diffs”.
      - “Answer open questions”.

#### 7.2 Clarifying Questions Queue

- Integrated in right panel (below document list) or as a collapsible section:
  - Header: **“Clarifying Questions”**.
  - Each question row:
    - Question text (single or multi-line).
    - Agent avatar + name.
    - Related doc chip (e.g. `Risk Register`, `The Pitch`).
    - Badge: **Blocking** or **Non-blocking**.
    - Optional small icon indicating if question has a draft answer.

- **Answer flow**
  - Clicking a question:
    - Focuses the main chat composer.
    - Prefills with quoted question and @mention of the asking agent.
  - After answering:
    - Question row updates to “Answered” state.
    - Blocking questions, once answered, clear the “Blocking” flag for related docs.

---

### 8. Visual Language & Agent Personas

- **Agent identity**
  - Each agent has:
    - Distinct color.
    - Iconography consistent across:
      - Avatars.
      - @mention pills.
      - Activity tags (edited, asked, proposed).
      - Diff cards they propose.
  - Example color mapping (tunable by design system):
    - Devil’s Advocate: red/orange (critical).
    - Angel Eyes: teal/blue (calm, constructive).
    - Capital Freak: green (money, unit economics).
    - Cake Man: purple/pink (delight, wow factor).
    - Buzz: yellow/orange (attention, marketing).
    - Mr. T: steel blue/gray (technical stability).
    - Maestro: neutral indigo (orchestrator).

- **Documents as living artifacts**
  - Standard icons and colors for:
    - Pitch, Risk, Business Model, Roadmap, GTM, Tech Spec, Open Questions.
  - Emphasis on:
    - Version labels (v1, v2, v7).
    - “Updated Xm ago by [Agent]” in list and document header.

---

### 9. Responsiveness

- **Desktop (primary)**
  - Full 3-column layout (left sessions, center chat, right docs/diffs).

- **Tablet**
  - Left panel collapsible into a slide-out drawer.
  - Right panel (docs) becomes a toggleable pane or overlay:
    - Button “Show docs” in top app bar.

- **Mobile**
  - Stacked views with bottom navigation or segmented control:
    - Tabs: **Chat**, **Docs**, **Questions**.
  - @mentions and diff approvals:
    - Handled via full-screen sheets or drawers.
  - Keep essential elements:
    - Agent avatars and roles on messages.
    - Basic doc status and approvals.

---

### 10. Intended Use with AI UI Designer

- This spec is designed to be **copy-pasted directly** into an AI UI design tool.
- Key requirements:
  - 3-column layout on desktop (chat history / main chat / docs).
  - Strong support for **agent @mentions** and **document #mentions**.
  - Integrated **approval UIs**, **content diffs**, and **review history**.
  - Clear visual mapping to concepts defined in `docs/02-agents-and-ux.md`.


