Multi-Agent ChangeSet Architecture v2 (LangGraph + React)

This is a rewritten, end-to-end implementation guide for a multi-agent system where:
	•	Specialist agents (e.g., Marketer, Tech Expert, Idea Improver) can update any document.
	•	Agents propose diff-reviewable changes across multiple documents and multiple locations.
	•	The UI presents a single approval that covers all proposed changes.
	•	Changes are applied/persisted only after approval.
	•	The system streams UI events to a React frontend.

The architecture is designed to be:
	•	Auditable (every proposed change is reviewable)
	•	Deterministic (diffs computed from authoritative state)
	•	Low-friction (agents don’t output old snippets or byte offsets)
	•	UI-friendly (streamed events + a clear approval step)

⸻

1) High-level flow
	1.	User asks for updates
	2.	Supervisor chooses a specialist agent
	3.	Specialist calls propose_edits (tool) with edits for one or more docs
	4.	System node build_changeset computes unified diffs and creates a single pending_change_set
	5.	System node await_approval interrupts execution and sends ChangeSet to UI
	6.	React UI shows diffs (tabs by doc) and user clicks Approve or Reject
	7.	Graph resumes:
	•	Approve → apply_changeset (mutate authoritative docs + persist)
	•	Reject → reject_changeset (discard)
	8.	Supervisor decides if more work is needed or finish

⸻

2) Key data structures

2.1 Documents (authoritative)

Documents are the persisted truth.

Doc {
  title: string
  content: string
  doc_type: string
  updated_by: string
  updated_at: ISODate
}

// stored in state
docs: Record<doc_id, Doc>

2.2 Unified diff (review format)

A unified diff is the familiar git diff style output with hunks:

--- a/pitch
+++ b/pitch
@@ -10,7 +10,9 @@
-We help teams ship faster.
+We help teams ship faster by automating QA.
+Built for startups shipping weekly.

	•	One doc diff may include multiple hunks (different locations)
	•	This is ideal for UI review

2.3 ChangeSet (single approval unit)

A ChangeSet groups all edits awaiting approval.

ChangeSet {
  change_set_id: string
  created_by: string
  created_at: ISODate
  summary: string

  // the actual proposed new content per doc
  edits: Array<{ doc_id: string; new_content: string }>

  // computed for UI review
  diffs: Record<doc_id, UnifiedDiffString>

  status: "pending" | "approved" | "rejected"
}

Only one exists at a time:

pending_change_set: ChangeSet | null


⸻

3) LangGraph state shape (Option A)

Option A: the agent tool is declarative. It stages proposals; system nodes do diffs/approval/persistence.

from typing import TypedDict, Annotated, Optional
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class Doc(TypedDict):
    title: str
    content: str
    doc_type: str
    updated_by: str
    updated_at: str  # ISO

class ProposedEdit(TypedDict):
    doc_id: str
    new_content: str

class ChangeSet(TypedDict):
    change_set_id: str
    created_by: str
    created_at: str
    summary: str
    edits: list[ProposedEdit]
    diffs: dict[str, str]  # doc_id -> unified diff
    status: str            # pending/approved/rejected

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # authoritative docs (persist these)
    docs: dict[str, Doc]

    # staging area (ephemeral)
    proposed_edits: Annotated[list[ProposedEdit], operator.add]
    proposal_summary: str
    proposal_by: str

    # approval unit
    pending_change_set: Optional[ChangeSet]

Notes:
	•	proposed_edits is append-only so multiple proposals can accumulate before building a ChangeSet.
	•	If you want exactly one specialist per ChangeSet, clear staging immediately after building.

⸻

4) Streaming events for React UI

Use LangGraph streaming with stream_mode=["custom", "updates"].

4.1 Custom event helper

from langgraph.config import get_stream_writer

def emit(event_type: str, payload: dict):
    w = get_stream_writer()
    if w:
        w({"type": event_type, **payload})

4.2 Recommended event types

agent.started
agent.proposed_edits
changeset.created
changeset.ready_for_review
changeset.approved
changeset.rejected
changeset.applied
changeset.discarded

Your React UI can:
	•	Show an activity feed from custom events
	•	Show approval UI when changeset.ready_for_review arrives
	•	Update doc panels when updates include docs

⸻

5) Agent-facing tool: propose_edits (Option A)

This is the only tool specialists need.
	•	Accepts edits across multiple docs
	•	Does not compute diffs
	•	Does not mutate authoritative docs
	•	Routes to build_changeset

from langchain_core.tools import tool
from langgraph.types import Command

@tool
def propose_edits(edits: list[dict], summary: str, by: str) -> Command:
    """Propose edits to one or more documents. Does not mutate docs."""

    emit("agent.proposed_edits", {
        "by": by,
        "docs": [e.get("doc_id") for e in edits],
        "summary": summary,
    })

    # Minimal validation (raise or drop invalid entries if you prefer)
    staged = [{"doc_id": e["doc_id"], "new_content": e["new_content"]} for e in edits]

    return Command(
        update={
            "proposed_edits": staged,
            "proposal_summary": summary,
            "proposal_by": by,
        },
        goto="build_changeset",
    )

Prompting specialists to use the tool

In each specialist prompt, include something like:
	•	“You may update any docs you think help.”
	•	“When ready, call propose_edits with one entry per doc you changed.”
	•	“Keep summaries short and specific.”

⸻

6) System nodes

6.1 build_changeset — compute unified diffs, create pending ChangeSet

This node:
	•	Reads authoritative docs (state.docs)
	•	Reads staging fields (proposed_edits, proposal_*)
	•	Produces a single pending_change_set with per-doc unified diffs

from difflib import unified_diff
from datetime import datetime, timezone
import uuid

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def build_changeset_node(state: State) -> dict:
    edits = state.get("proposed_edits", [])
    if not edits:
        return {}

    # Coalesce multiple proposals per doc (last write wins).
    # If you want to merge instead, do it here.
    latest_by_doc: dict[str, str] = {}
    for e in edits:
        latest_by_doc[e["doc_id"]] = e["new_content"]

    diffs: dict[str, str] = {}
    finalized_edits: list[ProposedEdit] = []

    for doc_id, new_content in latest_by_doc.items():
        old_content = state["docs"].get(doc_id, {}).get("content", "")
        diff = "".join(
            unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{doc_id}",
                tofile=f"b/{doc_id}",
            )
        )
        diffs[doc_id] = diff
        finalized_edits.append({"doc_id": doc_id, "new_content": new_content})

    cs_id = str(uuid.uuid4())
    changeset: ChangeSet = {
        "change_set_id": cs_id,
        "created_by": state.get("proposal_by", "agent"),
        "created_at": now_iso(),
        "summary": state.get("proposal_summary", ""),
        "edits": finalized_edits,
        "diffs": diffs,
        "status": "pending",
    }

    emit("changeset.created", {
        "change_set_id": cs_id,
        "created_by": changeset["created_by"],
        "docs": list(latest_by_doc.keys()),
        "summary": changeset["summary"],
    })

    return {
        "pending_change_set": changeset,
        # clear staging
        "proposed_edits": [],
        "proposal_summary": "",
        "proposal_by": "",
    }

6.2 await_approval — interrupt and wait for UI

This node pauses execution and returns a payload to your server/UI layer.
When the user clicks approve/reject, your server resumes the graph and provides the decision.

from langgraph.types import interrupt, Command

def await_approval_node(state: State):
    cs = state.get("pending_change_set")
    if not cs or cs.get("status") != "pending":
        return {}

    emit("changeset.ready_for_review", {
        "change_set_id": cs["change_set_id"],
        "docs": [e["doc_id"] for e in cs["edits"]],
    })

    decision = interrupt({
        "type": "approval_required",
        "change_set": {
            "change_set_id": cs["change_set_id"],
            "summary": cs["summary"],
            "diffs": cs["diffs"],
            "docs": [e["doc_id"] for e in cs["edits"]],
        },
    })

    # Resume expects: {"decision": "approve"} or {"decision": "reject"}
    if isinstance(decision, dict) and decision.get("decision") == "approve":
        emit("changeset.approved", {"change_set_id": cs["change_set_id"]})
        return Command(goto="apply_changeset")

    emit("changeset.rejected", {"change_set_id": cs["change_set_id"]})
    return Command(goto="reject_changeset")

6.3 apply_changeset — mutate authoritative docs and persist

On approval, we apply by overwriting doc content with the stored new_content.
Diffs are for review only.

from datetime import datetime, timezone

def apply_changeset_node(state: State) -> dict:
    cs = state.get("pending_change_set")
    if not cs:
        return {}

    updates: dict[str, Doc] = {}
    for e in cs["edits"]:
        doc_id = e["doc_id"]
        old = state["docs"].get(doc_id)
        if not old:
            continue

        new_doc = dict(old)
        new_doc["content"] = e["new_content"]
        new_doc["updated_by"] = cs.get("created_by", "agent")
        new_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        updates[doc_id] = new_doc

    emit("changeset.applied", {
        "change_set_id": cs["change_set_id"],
        "docs": list(updates.keys()),
    })

    merged_docs = dict(state["docs"])
    merged_docs.update(updates)

    # TODO: persist merged_docs (or updates) to your DB here
    return {
        "docs": merged_docs,
        "pending_change_set": None,
    }

6.4 reject_changeset — discard

def reject_changeset_node(state: State) -> dict:
    cs = state.get("pending_change_set")
    if cs:
        emit("changeset.discarded", {"change_set_id": cs["change_set_id"]})
    return {"pending_change_set": None}


⸻

7) Supervisor + specialists (routing)

7.1 Supervisor responsibility

Supervisor decides which specialist should act next. It does not edit docs.

Routing via handoff tools (return Command(goto=...)):
	•	to_marketer()
	•	to_tech_expert()
	•	to_idea_improver()
	•	finish()

7.2 Specialists responsibility

Specialists:
	•	read current docs (provide them in prompt context)
	•	propose edits using propose_edits

A specialist can update:
	•	multiple docs
	•	multiple locations per doc (unified diff will show multiple hunks)

⸻

8) Graph wiring (recommended)

A typical wiring:
	•	START -> supervisor
	•	supervisor -> marketer|tech_expert|idea_improver|final
	•	specialist -> build_changeset -> await_approval -> apply_changeset|reject_changeset -> supervisor

Implementation sketch:

from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)

builder.add_node("supervisor", supervisor_agent)
builder.add_node("marketer", marketer_agent)
builder.add_node("tech_expert", tech_expert_agent)
builder.add_node("idea_improver", idea_improver_agent)

builder.add_node("build_changeset", build_changeset_node)
builder.add_node("await_approval", await_approval_node)
builder.add_node("apply_changeset", apply_changeset_node)
builder.add_node("reject_changeset", reject_changeset_node)

builder.add_node("final", lambda s: {})

builder.add_edge(START, "supervisor")

# After changeset built, always go to approval
builder.add_edge("build_changeset", "await_approval")

# After apply/reject, return to supervisor
builder.add_edge("apply_changeset", "supervisor")
builder.add_edge("reject_changeset", "supervisor")

builder.add_edge("final", END)

graph = builder.compile()

Note: propose_edits returns Command(goto="build_changeset"), so specialists can jump straight into the pipeline.

⸻

9) React UI implementation guide

9.1 Streaming from the backend

Stream graph output with:
	•	custom events → activity feed, transitions
	•	updates → update document panels

Your backend likely exposes an endpoint that proxies LangGraph streaming over:
	•	Server-Sent Events (SSE) or
	•	WebSocket

9.2 UI state model

Maintain a client store like:

{
  docs: Record<string, Doc>
  pendingChangeSet?: ChangeSet
  activity: Array<{ type: string; ts: number; payload: any }>
}

Update rules:
	•	On custom event: append to activity; if changeset.ready_for_review, open approval drawer.
	•	On updates chunk containing docs: merge docs into UI state.
	•	On interrupt payload: set pendingChangeSet.

9.3 Approval drawer

Approval UI should show:
	•	ChangeSet summary
	•	Doc tabs (one per doc)
	•	Unified diff viewer for each doc

On Approve/Reject:
	•	POST to backend: { change_set_id, decision: "approve" | "reject" }
	•	Backend resumes graph with resume={"decision": ...}

9.4 Diff rendering options

You can render unified diff strings directly, or render from old/new content.
Practical approach:
	•	Use unified diff for the review display
	•	If your diff viewer prefers old/new: your backend can provide both (old from docs, new from edits)

⸻

10) Practical policies / edge cases

10.1 Ensure only one pending ChangeSet exists

Supervisor should avoid calling specialists while pending_change_set is pending.

10.2 Coalescing edits per doc

If multiple proposals for the same doc arrive before building the changeset:
	•	simplest: last write wins (current code)
	•	alternative: merge / pick best

10.3 Large docs / token cost

MVP: agent returns full new_content per doc.
Optimization path:
	•	switch to section-based edits (replace heading blocks)
	•	reconstruct full doc server-side and still compute unified diff

⸻

11) What to implement first (MVP checklist)
	1.	docs in state + persistence for docs
	2.	propose_edits tool
	3.	build_changeset node with unified diffs
	4.	await_approval interrupt/resume plumbing
	5.	React approval drawer with diff viewer
	6.	apply_changeset writes docs + persists
	7.	Stream events to show progress

⸻

12) Why this works
	•	Specialists are not tied to specific docs
	•	One approval covers all docs and hunks
	•	Diffs are deterministic and cheap (computed from state)
	•	UI is clean: “Review changes” is a single, trustable step
	•	Applying is robust: overwrite with approved new_content