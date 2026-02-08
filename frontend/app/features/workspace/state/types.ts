export type ChatRole = "user" | "assistant" | "tool" | "system";
export type StreamStatus = "idle" | "streaming" | "error";
export type RunStatus = "queued" | "running" | "waiting_approval" | "completed" | "error";
export type AgentLifecycleStatus =
  | "queued"
  | "thinking"
  | "tool_call"
  | "waiting_approval"
  | "done"
  | "error";
export type ChangeSetStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "request_changes"
  | "applied";

export interface ThreadEntity {
  id: string;
  title: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  lastMessagePreview: string | null;
}

export interface DocEntity {
  id: string;
  threadId: string;
  docId: string;
  title: string;
  content: string;
  description: string;
  version: number;
  updatedBy: string | null;
  updatedAt: string | null;
  createdAt: string | null;
}

export interface RunEntity {
  id: string;
  threadId: string;
  trigger: string;
  status: RunStatus;
  startedAt: string;
  completedAt: string | null;
  error: string | null;
}

export interface AgentStatusEntity {
  id: string;
  runId: string;
  threadId: string;
  agent: string;
  status: AgentLifecycleStatus;
  note: string | null;
  at: string;
}

export interface ChangeSetEntity {
  id: string;
  threadId: string;
  runId: string | null;
  interruptId?: string | null;
  createdBy: string;
  summary: string;
  status: ChangeSetStatus;
  createdAt: string | null;
  decidedAt: string | null;
  decisionNote: string | null;
  docs: string[];
  diffs: Record<string, string>;
  docChanges: ChangeSetDocChange[];
  reviews: ChangeSetReview[];
}

export interface ChangeSetDocChange {
  docId: string;
  beforeContent: string;
  afterContent: string;
  diff: string;
}

export interface ChangeSetReview {
  decision: string;
  comment: string | null;
  reviewedBy: string | null;
  reviewedAt: string | null;
}

export interface UiMessage {
  id: string;
  runId: string | null;
  role: ChatRole;
  byAgent?: string | null;
  content: string;
  createdAt: number;
  isStreaming?: boolean;
}

export interface ToolTimelineItem {
  id: string;
  runId: string | null;
  eventType: "tool.call" | "tool.result";
  createdAt: number;
  byAgent?: string | null;
  label: string;
  payload: unknown;
}

export interface PendingApproval {
  runId: string | null;
  changeSetId: string;
  interruptId?: string | null;
  summary: string;
  docs: string[];
  diffs: Record<string, string>;
  raw: unknown;
}

export interface WorkspaceState {
  threads: Record<string, ThreadEntity>;
  activeThreadId: string | null;
  docs: Record<string, DocEntity>;
  runs: Record<string, RunEntity>;
  agentStatuses: Record<string, AgentStatusEntity>;
  changesets: Record<string, ChangeSetEntity>;
  messagesByThread: Record<string, UiMessage[]>;
  toolTimelineByRun: Record<string, ToolTimelineItem[]>;
  input: string;
  streamStatus: StreamStatus;
  error: string | null;
  currentRunId: string | null;
  seenEventIds: Record<string, true>;
  completedMessageIds: Record<string, true>;
}

export interface StreamEvent<T = unknown> {
  type: string;
  data: T;
}

export interface ThreadSnapshot {
  thread: PersistedThread | null;
  messages: PersistedMessageRow[];
  docs: PersistedDocRow[];
  runs: PersistedRunRow[];
  agent_statuses: PersistedAgentStatusRow[];
  changesets: PersistedChangeSetRow[];
}

export interface PersistedThread {
  thread_id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
}

export interface PersistedMessageRow {
  message_id?: string;
  thread_id?: string;
  run_id?: string | null;
  seq?: number;
  role?: string;
  content?: { text?: unknown; blocks?: unknown };
  by_agent?: string | null;
  created_at?: string;
}

export interface PersistedDocRow {
  thread_id: string;
  doc_id: string;
  title: string;
  content: string;
  description: string;
  version: number;
  updated_by: string | null;
  updated_at: string | null;
  created_at: string | null;
}

export interface PersistedRunRow {
  run_id: string;
  thread_id: string;
  trigger: string;
  status: RunStatus;
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface PersistedAgentStatusRow {
  run_id: string;
  thread_id: string;
  agent: string;
  status: AgentLifecycleStatus;
  note: string | null;
  at: string;
}

export interface PersistedChangeSetRow {
  change_set_id: string;
  thread_id: string;
  run_id: string | null;
  created_by: string;
  summary: string;
  status: ChangeSetStatus;
  created_at: string | null;
  decided_at: string | null;
  decision_note: string | null;
  docs: string[];
  diffs: Record<string, string>;
  doc_changes?: PersistedChangeSetDocRow[];
  reviews?: PersistedChangeSetReviewRow[];
}

export interface PersistedChangeSetDocRow {
  doc_id: string;
  before_content: string;
  after_content: string;
  diff: string;
}

export interface PersistedChangeSetReviewRow {
  decision: string;
  comment: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
}
