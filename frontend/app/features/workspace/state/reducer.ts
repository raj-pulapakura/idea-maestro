import {
  AgentStatusEntity,
  ChangeSetEntity,
  PendingApproval,
  RunEntity,
  StreamEvent,
  ThreadSnapshot,
  ToolTimelineItem,
  UiMessage,
  WorkspaceState,
} from "@/app/features/workspace/state/types";

export type WorkspaceAction =
  | {
      type: "hydrateThreads";
      threads: NonNullable<ThreadSnapshot["thread"]>[];
    }
  | { type: "setActiveThread"; threadId: string }
  | { type: "setInput"; input: string }
  | {
      type: "hydrateDocs";
      threadId: string;
      docs: ThreadSnapshot["docs"];
    }
  | {
      type: "hydrateChangesets";
      threadId: string;
      changesets: ThreadSnapshot["changesets"];
    }
  | {
      type: "upsertDoc";
      doc: ThreadSnapshot["docs"][number];
    }
  | {
      type: "hydrateSnapshot";
      threadId: string;
      snapshot: ThreadSnapshot;
      messages: UiMessage[];
    }
  | { type: "pushUserMessage"; threadId: string; message: UiMessage }
  | { type: "beginStream" }
  | { type: "streamEvent"; event: StreamEvent }
  | { type: "streamError"; error: string }
  | { type: "streamDone" };

export function createInitialWorkspaceState(): WorkspaceState {
  return {
    threads: {},
    activeThreadId: null,
    docs: {},
    runs: {},
    agentStatuses: {},
    changesets: {},
    messagesByThread: {},
    toolTimelineByRun: {},
    input: "",
    streamStatus: "idle",
    error: null,
    currentRunId: null,
    seenEventIds: {},
    completedMessageIds: {},
  };
}

function toEventTimestamp(value: unknown, fallback: number): number {
  if (typeof value !== "string") {
    return fallback;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? fallback : parsed;
}

function ensureThread(
  state: WorkspaceState,
  threadId: string,
): WorkspaceState["threads"] {
  const nextThreads = { ...state.threads };
  if (!nextThreads[threadId]) {
    nextThreads[threadId] = {
      id: threadId,
      title: "Untitled Thread",
      status: "active",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastMessagePreview: null,
    };
  }
  return nextThreads;
}

function upsertMessage(
  messages: UiMessage[],
  messageId: string,
  update: Partial<UiMessage> & Pick<UiMessage, "id" | "role">,
): UiMessage[] {
  const index = messages.findIndex((msg) => msg.id === messageId);
  if (index < 0) {
    return [
      ...messages,
      {
        id: update.id,
        runId: update.runId ?? null,
        role: update.role,
        byAgent: update.byAgent ?? null,
        content: update.content ?? "",
        createdAt: update.createdAt ?? Date.now(),
        isStreaming: update.isStreaming ?? false,
      },
    ];
  }

  const copy = [...messages];
  copy[index] = { ...copy[index], ...update };
  return copy;
}

function buildToolItem(
  event: StreamEvent,
  runId: string | null,
  createdAt: number,
): ToolTimelineItem {
  const payload = (event.data ?? {}) as Record<string, unknown>;
  const toolCall = payload.tool_call as { name?: string } | undefined;
  const toolNameRaw = payload.tool_name ?? toolCall?.name ?? "tool";
  const toolName =
    typeof toolNameRaw === "string" && toolNameRaw.length > 0
      ? toolNameRaw
      : "tool";

  return {
    id: crypto.randomUUID(),
    runId,
    eventType: event.type === "tool.call" ? "tool.call" : "tool.result",
    createdAt,
    byAgent:
      typeof payload.by_agent === "string"
        ? payload.by_agent
        : typeof payload.byAgent === "string"
          ? payload.byAgent
          : null,
    label:
      event.type === "tool.call"
        ? `Calling ${toolName}`
        : `Result from ${toolName}`,
    payload: event.data,
  };
}

function upsertRun(
  runs: WorkspaceState["runs"],
  runId: string,
  patch: Partial<RunEntity>,
): WorkspaceState["runs"] {
  const existing = runs[runId];
  const next: RunEntity = {
    id: runId,
    threadId: patch.threadId ?? existing?.threadId ?? "",
    trigger: patch.trigger ?? existing?.trigger ?? "chat",
    status: patch.status ?? existing?.status ?? "queued",
    startedAt: patch.startedAt ?? existing?.startedAt ?? new Date().toISOString(),
    completedAt:
      patch.completedAt !== undefined
        ? patch.completedAt
        : existing?.completedAt ?? null,
    error: patch.error !== undefined ? patch.error : existing?.error ?? null,
  };

  return {
    ...runs,
    [runId]: next,
  };
}

function upsertAgentStatus(
  agentStatuses: WorkspaceState["agentStatuses"],
  nextStatus: AgentStatusEntity,
): WorkspaceState["agentStatuses"] {
  return {
    ...agentStatuses,
    [nextStatus.id]: nextStatus,
  };
}

function upsertChangeset(
  changesets: WorkspaceState["changesets"],
  patch: Partial<ChangeSetEntity> & Pick<ChangeSetEntity, "id" | "threadId">,
): WorkspaceState["changesets"] {
  const existing = changesets[patch.id];
  return {
    ...changesets,
    [patch.id]: {
      id: patch.id,
      threadId: patch.threadId,
      runId: patch.runId !== undefined ? patch.runId : existing?.runId ?? null,
      interruptId:
        patch.interruptId !== undefined
          ? patch.interruptId
          : existing?.interruptId ?? null,
      createdBy:
        patch.createdBy !== undefined
          ? patch.createdBy
          : existing?.createdBy ?? "agent",
      summary: patch.summary !== undefined ? patch.summary : existing?.summary ?? "",
      status: patch.status !== undefined ? patch.status : existing?.status ?? "pending",
      createdAt:
        patch.createdAt !== undefined ? patch.createdAt : existing?.createdAt ?? null,
      decidedAt:
        patch.decidedAt !== undefined ? patch.decidedAt : existing?.decidedAt ?? null,
      decisionNote:
        patch.decisionNote !== undefined
          ? patch.decisionNote
          : existing?.decisionNote ?? null,
      docs: patch.docs !== undefined ? patch.docs : existing?.docs ?? [],
      diffs: patch.diffs !== undefined ? patch.diffs : existing?.diffs ?? {},
      docChanges:
        patch.docChanges !== undefined ? patch.docChanges : existing?.docChanges ?? [],
      reviews: patch.reviews !== undefined ? patch.reviews : existing?.reviews ?? [],
    },
  };
}

export function getPendingApproval(
  state: WorkspaceState,
  threadId: string | null,
): PendingApproval | null {
  if (!threadId) {
    return null;
  }

  const pending = Object.values(state.changesets)
    .filter((changeset) => changeset.threadId === threadId)
    .find((changeset) => changeset.status === "pending");

  if (!pending) {
    return null;
  }

  return {
    runId: pending.runId,
    changeSetId: pending.id,
    interruptId: pending.interruptId ?? null,
    summary: pending.summary,
    docs: pending.docs,
    diffs: pending.diffs,
    raw: pending,
  };
}

export function workspaceReducer(
  state: WorkspaceState,
  action: WorkspaceAction,
): WorkspaceState {
  switch (action.type) {
    case "hydrateThreads": {
      const nextThreads = { ...state.threads };
      for (const thread of action.threads) {
        nextThreads[thread.thread_id] = {
          id: thread.thread_id,
          title: thread.title,
          status: thread.status,
          createdAt: thread.created_at,
          updatedAt: thread.updated_at,
          lastMessagePreview: thread.last_message_preview,
        };
      }
      return {
        ...state,
        threads: nextThreads,
      };
    }
    case "setActiveThread":
      return {
        ...state,
        activeThreadId: action.threadId,
        threads: ensureThread(state, action.threadId),
      };
    case "setInput":
      return { ...state, input: action.input };
    case "hydrateDocs": {
      const nextDocs = { ...state.docs };
      for (const doc of action.docs) {
        const key = `${doc.thread_id}:${doc.doc_id}`;
        nextDocs[key] = {
          id: key,
          threadId: doc.thread_id,
          docId: doc.doc_id,
          title: doc.title,
          content: doc.content,
          description: doc.description,
          version: doc.version,
          updatedBy: doc.updated_by,
          updatedAt: doc.updated_at,
          createdAt: doc.created_at,
        };
      }
      return {
        ...state,
        docs: nextDocs,
      };
    }
    case "upsertDoc": {
      const doc = action.doc;
      const key = `${doc.thread_id}:${doc.doc_id}`;
      return {
        ...state,
        docs: {
          ...state.docs,
          [key]: {
            id: key,
            threadId: doc.thread_id,
            docId: doc.doc_id,
            title: doc.title,
            content: doc.content,
            description: doc.description,
            version: doc.version,
            updatedBy: doc.updated_by,
            updatedAt: doc.updated_at,
            createdAt: doc.created_at,
          },
        },
      };
    }
    case "hydrateChangesets": {
      let nextChangesets = { ...state.changesets };
      for (const changeset of action.changesets) {
        nextChangesets = upsertChangeset(nextChangesets, {
          id: changeset.change_set_id,
          threadId: action.threadId,
          runId: changeset.run_id,
          createdBy: changeset.created_by,
          summary: changeset.summary,
          status: changeset.status,
          createdAt: changeset.created_at,
          decidedAt: changeset.decided_at,
          decisionNote: changeset.decision_note,
          docs: changeset.docs,
          diffs: changeset.diffs,
          docChanges:
            changeset.doc_changes?.map((docChange) => ({
              docId: docChange.doc_id,
              beforeContent: docChange.before_content,
              afterContent: docChange.after_content,
              diff: docChange.diff,
            })) ?? undefined,
          reviews:
            changeset.reviews?.map((review) => ({
              decision: review.decision,
              comment: review.comment,
              reviewedBy: review.reviewed_by,
              reviewedAt: review.reviewed_at,
            })) ?? undefined,
        });
      }
      return {
        ...state,
        changesets: nextChangesets,
      };
    }
    case "hydrateSnapshot": {
      const { snapshot, threadId, messages } = action;
      const nextThreads = ensureThread(state, threadId);

      if (snapshot.thread) {
        nextThreads[threadId] = {
          id: snapshot.thread.thread_id,
          title: snapshot.thread.title,
          status: snapshot.thread.status,
          createdAt: snapshot.thread.created_at,
          updatedAt: snapshot.thread.updated_at,
          lastMessagePreview: snapshot.thread.last_message_preview,
        };
      }

      const nextDocs = { ...state.docs };
      for (const doc of snapshot.docs) {
        const key = `${doc.thread_id}:${doc.doc_id}`;
        nextDocs[key] = {
          id: key,
          threadId: doc.thread_id,
          docId: doc.doc_id,
          title: doc.title,
          content: doc.content,
          description: doc.description,
          version: doc.version,
          updatedBy: doc.updated_by,
          updatedAt: doc.updated_at,
          createdAt: doc.created_at,
        };
      }

      let nextRuns = { ...state.runs };
      for (const run of snapshot.runs) {
        nextRuns = upsertRun(nextRuns, run.run_id, {
          threadId: run.thread_id,
          trigger: run.trigger,
          status: run.status,
          startedAt: run.started_at,
          completedAt: run.completed_at,
          error: run.error,
        });
      }

      let nextStatuses = { ...state.agentStatuses };
      for (const agentStatus of snapshot.agent_statuses) {
        const id = `${agentStatus.run_id}:${agentStatus.agent}`;
        nextStatuses = upsertAgentStatus(nextStatuses, {
          id,
          runId: agentStatus.run_id,
          threadId: agentStatus.thread_id,
          agent: agentStatus.agent,
          status: agentStatus.status,
          note: agentStatus.note,
          at: agentStatus.at,
        });
      }

      let nextChangesets = { ...state.changesets };
      for (const changeset of snapshot.changesets) {
        nextChangesets = upsertChangeset(nextChangesets, {
          id: changeset.change_set_id,
          threadId: changeset.thread_id,
          runId: changeset.run_id,
          createdBy: changeset.created_by,
          summary: changeset.summary,
          status: changeset.status,
          createdAt: changeset.created_at,
          decidedAt: changeset.decided_at,
          decisionNote: changeset.decision_note,
          docs: changeset.docs,
          diffs: changeset.diffs,
          docChanges:
            changeset.doc_changes?.map((docChange) => ({
              docId: docChange.doc_id,
              beforeContent: docChange.before_content,
              afterContent: docChange.after_content,
              diff: docChange.diff,
            })) ?? undefined,
          reviews:
            changeset.reviews?.map((review) => ({
              decision: review.decision,
              comment: review.comment,
              reviewedBy: review.reviewed_by,
              reviewedAt: review.reviewed_at,
            })) ?? undefined,
        });
      }

      return {
        ...state,
        activeThreadId: threadId,
        threads: nextThreads,
        docs: nextDocs,
        runs: nextRuns,
        agentStatuses: nextStatuses,
        changesets: nextChangesets,
        messagesByThread: {
          ...state.messagesByThread,
          [threadId]: messages,
        },
      };
    }
    case "pushUserMessage": {
      const current = state.messagesByThread[action.threadId] ?? [];
      return {
        ...state,
        messagesByThread: {
          ...state.messagesByThread,
          [action.threadId]: [...current, action.message],
        },
      };
    }
    case "beginStream":
      return { ...state, streamStatus: "streaming", error: null };
    case "streamDone":
      if (state.streamStatus === "error") {
        return state;
      }
      return { ...state, streamStatus: "idle" };
    case "streamError":
      return { ...state, streamStatus: "error", error: action.error };
    case "streamEvent": {
      const { event } = action;
      const payload = (event.data ?? {}) as Record<string, unknown>;
      const threadId =
        typeof payload.thread_id === "string"
          ? payload.thread_id
          : state.activeThreadId;
      const runId =
        typeof payload.run_id === "string" ? payload.run_id : state.currentRunId;
      const fallbackNow = Date.now();
      const emittedAt = toEventTimestamp(payload.emitted_at, fallbackNow);
      const eventId = typeof payload.event_id === "string" ? payload.event_id : null;

      if (!threadId) {
        return state;
      }

      if (eventId && state.seenEventIds[eventId]) {
        return state;
      }

      const nextSeenEventIds = eventId
        ? { ...state.seenEventIds, [eventId]: true as const }
        : state.seenEventIds;

      let nextState: WorkspaceState = {
        ...state,
        threads: ensureThread(state, threadId),
        seenEventIds: nextSeenEventIds,
      };

      if (event.type === "run.started" && runId) {
        nextState = {
          ...nextState,
          currentRunId: runId,
          streamStatus: "streaming",
          error: null,
          runs: upsertRun(nextState.runs, runId, {
            threadId,
            status: "running",
            trigger: typeof payload.trigger === "string" ? payload.trigger : "chat",
            startedAt:
              typeof payload.started_at === "string"
                ? payload.started_at
                : new Date(emittedAt).toISOString(),
            completedAt: null,
            error: null,
          }),
        };
      }

      if (event.type === "agent.status" && runId) {
        const agent = typeof payload.agent === "string" ? payload.agent : "agent";
        const id = `${runId}:${agent}`;
        nextState = {
          ...nextState,
          agentStatuses: upsertAgentStatus(nextState.agentStatuses, {
            id,
            runId,
            threadId,
            agent,
            status:
              typeof payload.status === "string"
                ? (payload.status as AgentStatusEntity["status"])
                : "thinking",
            note: typeof payload.note === "string" ? payload.note : null,
            at:
              typeof payload.at === "string"
                ? payload.at
                : typeof payload.emitted_at === "string"
                  ? payload.emitted_at
                  : new Date(emittedAt).toISOString(),
          }),
        };
      }

      if (event.type === "keepalive") {
        return nextState;
      }

      if (event.type === "message.delta") {
        const messageId =
          typeof payload.message_id === "string"
            ? payload.message_id
            : crypto.randomUUID();
        const messageKey = `${threadId}:${messageId}`;
        if (nextState.completedMessageIds[messageKey]) {
          return nextState;
        }
        const delta = typeof payload.delta === "string" ? payload.delta : "";
        const byAgent =
          typeof payload.by_agent === "string"
            ? payload.by_agent
            : typeof payload.byAgent === "string"
              ? payload.byAgent
              : null;
        const currentMessages = nextState.messagesByThread[threadId] ?? [];
        const currentMessage = currentMessages.find((message) => message.id === messageId);
        const existingContent = currentMessage?.content ?? "";

        return {
          ...nextState,
          messagesByThread: {
            ...nextState.messagesByThread,
            [threadId]: upsertMessage(currentMessages, messageId, {
              id: messageId,
              runId,
              role: "assistant",
              byAgent,
              content: existingContent + delta,
              createdAt: currentMessage?.createdAt ?? emittedAt,
              isStreaming: true,
            }),
          },
        };
      }

      if (event.type === "message.completed") {
        const messageId =
          typeof payload.message_id === "string"
            ? payload.message_id
            : crypto.randomUUID();
        const messageKey = `${threadId}:${messageId}`;
        if (nextState.completedMessageIds[messageKey]) {
          return nextState;
        }
        const currentMessages = nextState.messagesByThread[threadId] ?? [];
        const currentMessage = currentMessages.find((message) => message.id === messageId);
        const content = typeof payload.content === "string" ? payload.content : "";
        const byAgent =
          typeof payload.by_agent === "string"
            ? payload.by_agent
            : typeof payload.byAgent === "string"
              ? payload.byAgent
              : null;

        return {
          ...nextState,
          completedMessageIds: {
            ...nextState.completedMessageIds,
            [messageKey]: true,
          },
          messagesByThread: {
            ...nextState.messagesByThread,
            [threadId]: upsertMessage(currentMessages, messageId, {
              id: messageId,
              runId,
              role: "assistant",
              byAgent,
              content: content || currentMessage?.content || "",
              createdAt: currentMessage?.createdAt ?? emittedAt,
              isStreaming: false,
            }),
          },
        };
      }

      if (event.type === "tool.call" || event.type === "tool.result") {
        const timelineRunId = runId ?? "orphan";
        const currentTools = nextState.toolTimelineByRun[timelineRunId] ?? [];

        return {
          ...nextState,
          toolTimelineByRun: {
            ...nextState.toolTimelineByRun,
            [timelineRunId]: [...currentTools, buildToolItem(event, runId, emittedAt)],
          },
        };
      }

      if (event.type === "changeset.created") {
        const changeSetId =
          typeof payload.change_set_id === "string"
            ? payload.change_set_id
            : crypto.randomUUID();

        return {
          ...nextState,
          changesets: upsertChangeset(nextState.changesets, {
            id: changeSetId,
            threadId,
            runId,
            createdBy:
              typeof payload.created_by === "string" ? payload.created_by : "agent",
            summary: typeof payload.summary === "string" ? payload.summary : "",
            status: "pending",
            createdAt:
              typeof payload.emitted_at === "string"
                ? payload.emitted_at
                : new Date(emittedAt).toISOString(),
            docs: Array.isArray(payload.docs)
              ? payload.docs.filter((doc): doc is string => typeof doc === "string")
              : [],
            docChanges: [],
            reviews: [],
          }),
        };
      }

      if (event.type === "approval.required") {
        const changeSetRaw =
          payload.change_set && typeof payload.change_set === "object"
            ? (payload.change_set as Record<string, unknown>)
            : null;

        if (!changeSetRaw) {
          return nextState;
        }

        const changeSetId =
          typeof changeSetRaw.change_set_id === "string"
            ? changeSetRaw.change_set_id
            : crypto.randomUUID();
        const diffs =
          changeSetRaw.diffs && typeof changeSetRaw.diffs === "object"
            ? (changeSetRaw.diffs as Record<string, string>)
            : {};

        return {
          ...nextState,
          streamStatus: "idle",
          changesets: upsertChangeset(nextState.changesets, {
            id: changeSetId,
            threadId,
            runId,
            interruptId:
              typeof payload.interrupt_id === "string"
                ? payload.interrupt_id
                : null,
            summary:
              typeof changeSetRaw.summary === "string"
                ? changeSetRaw.summary
                : "Pending edits",
            status: "pending",
            docs: Array.isArray(changeSetRaw.docs)
              ? changeSetRaw.docs.filter((doc): doc is string => typeof doc === "string")
              : [],
            diffs,
            createdAt:
              typeof payload.emitted_at === "string"
                ? payload.emitted_at
                : new Date(emittedAt).toISOString(),
            docChanges: [],
            reviews: [],
          }),
        };
      }

      if (
        event.type === "changeset.approved" ||
        event.type === "changeset.rejected" ||
        event.type === "changeset.request_changes" ||
        event.type === "changeset.applied"
      ) {
        const changeSetId =
          typeof payload.change_set_id === "string" ? payload.change_set_id : null;
        if (!changeSetId || !nextState.changesets[changeSetId]) {
          return nextState;
        }

        const statusByType: Record<string, ChangeSetEntity["status"]> = {
          "changeset.approved": "approved",
          "changeset.rejected": "rejected",
          "changeset.request_changes": "request_changes",
          "changeset.applied": "applied",
        };

        return {
          ...nextState,
          changesets: upsertChangeset(nextState.changesets, {
            id: changeSetId,
            threadId,
            status: statusByType[event.type],
            decidedAt:
              typeof payload.emitted_at === "string"
                ? payload.emitted_at
                : new Date(emittedAt).toISOString(),
          }),
        };
      }

      if (event.type === "run.error") {
        const error = typeof payload.error === "string" ? payload.error : "Run failed";
        if (!runId) {
          return { ...nextState, streamStatus: "error", error };
        }

        return {
          ...nextState,
          streamStatus: "error",
          error,
          currentRunId: null,
          runs: upsertRun(nextState.runs, runId, {
            threadId,
            status: "error",
            error,
            completedAt:
              typeof payload.completed_at === "string"
                ? payload.completed_at
                : new Date(emittedAt).toISOString(),
          }),
        };
      }

      if (event.type === "run.completed") {
        const status =
          payload.status === "waiting_approval" ? "waiting_approval" : "completed";

        if (!runId) {
          return {
            ...nextState,
            streamStatus: status === "waiting_approval" ? "idle" : "idle",
            currentRunId: null,
          };
        }

        return {
          ...nextState,
          streamStatus: "idle",
          currentRunId: null,
          runs: upsertRun(nextState.runs, runId, {
            threadId,
            status,
            completedAt:
              typeof payload.completed_at === "string"
                ? payload.completed_at
                : new Date(emittedAt).toISOString(),
          }),
        };
      }

      return nextState;
    }
    default:
      return state;
  }
}
