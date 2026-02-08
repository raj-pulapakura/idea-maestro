import {
  AgentStatusEntity,
  ChangeSetEntity,
  RunEntity,
  ToolTimelineItem,
} from "@/app/features/workspace/state/types";

export type RunLogEntryKind = "run" | "agent" | "tool" | "changeset";

export interface RunLogEntry {
  id: string;
  kind: RunLogEntryKind;
  createdAt: number;
  title: string;
  description: string;
  runId: string | null;
}

function toTimestamp(value: string | null | undefined): number {
  if (!value) {
    return 0;
  }
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function getToolDescription(tool: ToolTimelineItem): string {
  if (typeof tool.label === "string" && tool.label.trim().length > 0) {
    return tool.label;
  }
  return tool.eventType === "tool.call" ? "Tool call" : "Tool result";
}

export function buildRunLog(params: {
  threadId: string | null;
  runs: Record<string, RunEntity>;
  agentStatuses: Record<string, AgentStatusEntity>;
  toolTimelineByRun: Record<string, ToolTimelineItem[]>;
  changesets: Record<string, ChangeSetEntity>;
}): RunLogEntry[] {
  const { threadId, runs, agentStatuses, toolTimelineByRun, changesets } = params;
  if (!threadId) {
    return [];
  }

  const threadRuns = Object.values(runs).filter((run) => run.threadId === threadId);
  const runIds = new Set(threadRuns.map((run) => run.id));

  const entries: RunLogEntry[] = [];

  for (const run of threadRuns) {
    entries.push({
      id: `run:${run.id}:started`,
      kind: "run",
      createdAt: toTimestamp(run.startedAt),
      title: `Run started (${run.trigger})`,
      description: `Status: ${run.status.replaceAll("_", " ")}`,
      runId: run.id,
    });

    if (run.completedAt) {
      entries.push({
        id: `run:${run.id}:completed`,
        kind: "run",
        createdAt: toTimestamp(run.completedAt),
        title:
          run.status === "error"
            ? "Run failed"
            : run.status === "waiting_approval"
              ? "Run waiting approval"
              : "Run completed",
        description: run.error ?? `Status: ${run.status.replaceAll("_", " ")}`,
        runId: run.id,
      });
    }
  }

  for (const status of Object.values(agentStatuses)) {
    if (!runIds.has(status.runId)) {
      continue;
    }
    entries.push({
      id: `agent:${status.id}:${status.at}`,
      kind: "agent",
      createdAt: toTimestamp(status.at),
      title: `${status.agent} status`,
      description: `${status.status.replaceAll("_", " ")}${status.note ? ` - ${status.note}` : ""}`,
      runId: status.runId,
    });
  }

  for (const [runId, tools] of Object.entries(toolTimelineByRun)) {
    if (runId !== "orphan" && !runIds.has(runId)) {
      continue;
    }
    for (const tool of tools) {
      entries.push({
        id: `tool:${tool.id}`,
        kind: "tool",
        createdAt: tool.createdAt,
        title: tool.eventType === "tool.call" ? "Tool call" : "Tool result",
        description: getToolDescription(tool),
        runId: tool.runId,
      });
    }
  }

  for (const changeset of Object.values(changesets)) {
    if (changeset.threadId !== threadId) {
      continue;
    }
    entries.push({
      id: `changeset:${changeset.id}:created`,
      kind: "changeset",
      createdAt: toTimestamp(changeset.createdAt),
      title: "Changeset created",
      description:
        changeset.summary || `${changeset.docs.length} doc(s) staged for review`,
      runId: changeset.runId,
    });

    if (changeset.decidedAt) {
      entries.push({
        id: `changeset:${changeset.id}:decided`,
        kind: "changeset",
        createdAt: toTimestamp(changeset.decidedAt),
        title: `Changeset ${changeset.status.replaceAll("_", " ")}`,
        description: changeset.decisionNote ?? "No decision note",
        runId: changeset.runId,
      });
    }
  }

  return entries.sort((a, b) => b.createdAt - a.createdAt);
}
