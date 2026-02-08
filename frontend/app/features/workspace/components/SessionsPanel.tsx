import { ThreadEntity } from "@/app/features/workspace/state/types";

interface SessionsPanelProps {
  threads: ThreadEntity[];
  activeThreadId: string | null;
  isStreaming: boolean;
  onToggleCollapse: () => void;
  onSelectThread: (threadId: string) => void;
  onCreateThread: () => Promise<void>;
}

export function SessionsPanel({
  threads,
  activeThreadId,
  isStreaming,
  onToggleCollapse,
  onSelectThread,
  onCreateThread,
}: SessionsPanelProps) {
  return (
    <aside className="app-scroll overflow-y-auto border-r border-[var(--border-weak)] bg-[var(--bg-panel)] p-3">
      <div className="mb-2 flex justify-end">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="rounded-md border border-[var(--border-weak)] bg-white px-2 py-1 text-xs font-semibold"
        >
          Collapse
        </button>
      </div>
      <button
        type="button"
        onClick={() => void onCreateThread()}
        disabled={isStreaming}
        className="mb-3 w-full rounded-xl bg-[var(--accent)] px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        + New Session
      </button>
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-[var(--text-secondary)]">
        Active Workspaces
      </p>
      <div className="space-y-2">
        {threads.length === 0 ? (
          <div className="rounded-xl border border-[var(--border-weak)] bg-white p-3 text-sm text-[var(--text-secondary)]">
            No sessions yet.
          </div>
        ) : null}
        {threads.map((thread) => {
          const isActive = thread.id === activeThreadId;
          return (
            <button
              key={thread.id}
              type="button"
              disabled={isStreaming && !isActive}
              onClick={() => onSelectThread(thread.id)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                isActive
                  ? "border-[var(--accent)] bg-white"
                  : "border-transparent bg-[var(--bg-muted)]"
              } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              <div className="flex items-center justify-between">
                <p className="truncate pr-2 text-sm font-semibold">{thread.title}</p>
                <span
                  className={`h-2 w-2 rounded-full ${
                    thread.status === "active" ? "bg-[var(--success)]" : "bg-slate-400"
                  }`}
                />
              </div>
              <p className="mt-1 truncate text-xs text-[var(--text-secondary)]">
                {thread.lastMessagePreview || "No messages yet"}
              </p>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
