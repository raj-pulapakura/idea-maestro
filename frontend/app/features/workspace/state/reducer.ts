import {
  ChatState,
  PendingApproval,
  StreamEvent,
  ToolTimelineItem,
  UiMessage,
} from "@/app/features/workspace/state/types";

export type ChatAction =
  | { type: "setThreadId"; threadId: string }
  | { type: "setInput"; input: string }
  | { type: "hydrateMessages"; messages: UiMessage[] }
  | { type: "pushUserMessage"; message: UiMessage }
  | { type: "startStream" }
  | { type: "streamEvent"; event: StreamEvent }
  | { type: "streamError"; error: string }
  | { type: "streamDone" };

export function createInitialChatState(threadId: string): ChatState {
  return {
    threadId,
    input: "",
    status: "idle",
    error: null,
    messages: [],
    toolTimeline: [],
    pendingApproval: null,
  };
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

function buildToolItem(event: StreamEvent): ToolTimelineItem {
  const payload = (event.data ?? {}) as Record<string, unknown>;
  const toolCall = payload.tool_call as { name?: string } | undefined;
  const toolNameRaw = payload.tool_name ?? toolCall?.name ?? "tool";
  const toolName =
    typeof toolNameRaw === "string" && toolNameRaw.length > 0
      ? toolNameRaw
      : "tool";

  return {
    id: crypto.randomUUID(),
    eventType: event.type === "tool.call" ? "tool.call" : "tool.result",
    createdAt: Date.now(),
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

function extractPendingApproval(data: unknown): PendingApproval | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const payload = data as Record<string, unknown>;
  const changeSetRaw =
    payload.change_set && typeof payload.change_set === "object"
      ? payload.change_set
      : null;
  if (!changeSetRaw) {
    return null;
  }

  const changeSet = changeSetRaw as Record<string, unknown>;
  const diffs =
    changeSet.diffs && typeof changeSet.diffs === "object"
      ? (changeSet.diffs as Record<string, string>)
      : {};

  return {
    changeSetId:
      typeof changeSet.change_set_id === "string"
        ? changeSet.change_set_id
        : crypto.randomUUID(),
    summary:
      typeof changeSet.summary === "string" ? changeSet.summary : "Pending edits",
    docs: Array.isArray(changeSet.docs)
      ? changeSet.docs.filter((doc): doc is string => typeof doc === "string")
      : [],
    diffs,
    raw: data,
  };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "setThreadId":
      return { ...state, threadId: action.threadId };
    case "setInput":
      return { ...state, input: action.input };
    case "hydrateMessages":
      return { ...state, messages: action.messages };
    case "pushUserMessage":
      return { ...state, messages: [...state.messages, action.message] };
    case "startStream":
      return { ...state, status: "streaming", error: null };
    case "streamDone":
      return { ...state, status: "idle" };
    case "streamError":
      return { ...state, status: "error", error: action.error };
    case "streamEvent": {
      const { event } = action;
      const payload = (event.data ?? {}) as Record<string, unknown>;

      if (event.type === "message.delta") {
        const messageId =
          typeof payload.message_id === "string"
            ? payload.message_id
            : crypto.randomUUID();
        const delta = typeof payload.delta === "string" ? payload.delta : "";
        const byAgent =
          typeof payload.by_agent === "string"
            ? payload.by_agent
            : typeof payload.byAgent === "string"
              ? payload.byAgent
              : null;
        const current = state.messages.find((msg) => msg.id === messageId);
        const existingContent = current?.content ?? "";

        return {
          ...state,
          messages: upsertMessage(state.messages, messageId, {
            id: messageId,
            role: "assistant",
            byAgent,
            content: existingContent + delta,
            isStreaming: true,
          }),
        };
      }

      if (event.type === "message.completed") {
        const messageId =
          typeof payload.message_id === "string"
            ? payload.message_id
            : crypto.randomUUID();
        const content = typeof payload.content === "string" ? payload.content : "";
        const byAgent =
          typeof payload.by_agent === "string"
            ? payload.by_agent
            : typeof payload.byAgent === "string"
              ? payload.byAgent
              : null;

        return {
          ...state,
          messages: upsertMessage(state.messages, messageId, {
            id: messageId,
            role: "assistant",
            byAgent,
            content,
            isStreaming: false,
          }),
        };
      }

      if (event.type === "tool.call" || event.type === "tool.result") {
        return {
          ...state,
          toolTimeline: [...state.toolTimeline, buildToolItem(event)],
        };
      }

      if (event.type === "approval.required") {
        return {
          ...state,
          pendingApproval: extractPendingApproval(event.data),
          status: "idle",
        };
      }

      if (event.type === "changeset.applied" || event.type === "changeset.discarded") {
        return {
          ...state,
          pendingApproval: null,
        };
      }

      if (event.type === "run.error") {
        const error = typeof payload.error === "string" ? payload.error : "Run failed";
        return { ...state, status: "error", error };
      }

      if (event.type === "run.completed") {
        return { ...state, status: "idle" };
      }

      return state;
    }
    default:
      return state;
  }
}
