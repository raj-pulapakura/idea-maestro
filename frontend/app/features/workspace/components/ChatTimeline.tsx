import { AGENT_COLOR } from "@/app/features/workspace/constants";
import { StreamStatus } from "@/app/features/workspace/state/types";
import { getAgentInitials } from "@/app/features/workspace/utils/message-mappers";
import { TimelineEntry } from "@/app/features/workspace/utils/timeline";

interface ChatTimelineProps {
  status: StreamStatus;
  error: string | null;
  timeline: TimelineEntry[];
}

export function ChatTimeline({ status, error, timeline }: ChatTimelineProps) {
  return (
    <div className="app-scroll min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-4">
      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {timeline.map((entry) => {
        if (entry.kind === "tool") {
          return (
            <div
              key={entry.id}
              className="rounded-xl border border-[var(--border-weak)] bg-[var(--bg-muted)] p-3 text-sm"
            >
              <p className="font-semibold">{entry.tool.label}</p>
              <p className="mt-1 text-xs text-[var(--text-secondary)]">
                {entry.tool.byAgent ? `by ${entry.tool.byAgent}` : "agent activity"}
              </p>
            </div>
          );
        }

        const message = entry.message;
        const isUser = message.role === "user";
        const avatarColor =
          AGENT_COLOR[message.byAgent ?? ""] ||
          (isUser ? "bg-slate-700" : "bg-indigo-500");

        return (
          <div
            key={entry.id}
            className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
          >
            {!isUser ? (
              <div
                className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold text-white ${avatarColor}`}
              >
                {getAgentInitials(message.byAgent)}
              </div>
            ) : null}
            <div
              className={`max-w-3xl rounded-2xl border p-4 text-[15px] ${
                isUser
                  ? "border-[var(--accent)] bg-[var(--accent)] text-white"
                  : "border-[var(--border-weak)] bg-[var(--bg-muted)] text-[var(--text-primary)]"
              }`}
            >
              <p className="mb-1 text-xs font-semibold opacity-75">
                {isUser ? "You" : message.byAgent || "Agent"}
                {message.isStreaming ? " · streaming" : ""}
              </p>
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        );
      })}

      {status === "streaming" ? (
        <p className="text-xs italic text-[var(--text-secondary)]">
          Agent response streaming...
        </p>
      ) : null}
    </div>
  );
}
