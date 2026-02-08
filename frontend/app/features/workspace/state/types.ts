export type ChatRole = "user" | "assistant" | "tool" | "system";
export type StreamStatus = "idle" | "streaming" | "error";

export interface UiMessage {
  id: string;
  role: ChatRole;
  byAgent?: string | null;
  content: string;
  createdAt: number;
  isStreaming?: boolean;
}

export interface ToolTimelineItem {
  id: string;
  eventType: "tool.call" | "tool.result";
  createdAt: number;
  byAgent?: string | null;
  label: string;
  payload: unknown;
}

export interface PendingApproval {
  changeSetId: string;
  summary: string;
  docs: string[];
  diffs: Record<string, string>;
  raw: unknown;
}

export interface ChatState {
  threadId: string;
  input: string;
  status: StreamStatus;
  error: string | null;
  messages: UiMessage[];
  toolTimeline: ToolTimelineItem[];
  pendingApproval: PendingApproval | null;
}

export interface StreamEvent<T = unknown> {
  type: string;
  data: T;
}

export interface PersistedMessageRow {
  role?: string;
  content?: { text?: unknown; blocks?: unknown };
  by_agent?: string | null;
}
