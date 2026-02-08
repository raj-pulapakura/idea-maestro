import { ChatState } from "@/app/features/workspace/state/types";
import { TimelineEntry } from "@/app/features/workspace/utils/timeline";
import { ChatComposer } from "@/app/features/workspace/components/ChatComposer";
import { ChatTimeline } from "@/app/features/workspace/components/ChatTimeline";

interface ChatPanelProps {
  state: ChatState;
  timeline: TimelineEntry[];
  canSend: boolean;
  onInputChange: (value: string) => void;
  onSend: () => Promise<void>;
}

export function ChatPanel({
  state,
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
          Thread: <span className="font-mono-ui">{state.threadId || "..."}</span>
        </p>
      </header>
      <ChatTimeline status={state.status} error={state.error} timeline={timeline} />
      <ChatComposer
        input={state.input}
        canSend={canSend}
        onInputChange={onInputChange}
        onSend={onSend}
      />
    </section>
  );
}
