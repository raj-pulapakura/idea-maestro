import {
  AgentStatusEntity,
  RunEntity,
  WorkspaceState,
} from "@/app/features/workspace/state/types";
import { TimelineEntry } from "@/app/features/workspace/utils/timeline";
import { ChatComposer } from "@/app/features/workspace/components/ChatComposer";
import { ChatTimeline } from "@/app/features/workspace/components/ChatTimeline";

interface ChatPanelProps {
  state: WorkspaceState;
  activeThreadId: string | null;
  latestRun: RunEntity | null;
  latestAgentStatuses: AgentStatusEntity[];
  timeline: TimelineEntry[];
  canSend: boolean;
  onInputChange: (value: string) => void;
  onSend: () => Promise<void>;
}

export function ChatPanel({
  state,
  activeThreadId,
  latestRun,
  latestAgentStatuses,
  timeline,
  canSend,
  onInputChange,
  onSend,
}: ChatPanelProps) {
  return (
    <section className="flex min-h-0 min-w-0 flex-col bg-[var(--bg-surface)]">
      <header className="border-b border-[var(--border-weak)] px-6 py-4">
        <p className="text-xl font-bold">Agent Workspace</p>
        <p className="text-xs text-[var(--text-secondary)]">
          Thread: <span className="font-mono-ui">{activeThreadId || "..."}</span>
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {latestRun ? (
            <span className="rounded-full bg-[var(--bg-muted)] px-2 py-1 text-[10px] font-semibold uppercase">
              Run: {latestRun.status.replace("_", " ")}
            </span>
          ) : null}
          {latestAgentStatuses.map((agentStatus) => (
            <span
              key={agentStatus.id}
              className="rounded-full border border-[var(--border-weak)] bg-white px-2 py-1 text-[10px] font-semibold"
            >
              {agentStatus.agent}: {agentStatus.status.replace("_", " ")}
            </span>
          ))}
        </div>
      </header>
      <ChatTimeline
        status={state.streamStatus}
        error={state.error}
        timeline={timeline}
      />
      <ChatComposer
        input={state.input}
        canSend={canSend}
        onInputChange={onInputChange}
        onSend={onSend}
      />
    </section>
  );
}
