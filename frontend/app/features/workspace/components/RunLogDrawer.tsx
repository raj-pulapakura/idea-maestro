import { RunLogEntry } from "@/app/features/workspace/utils/run-log";

interface RunLogDrawerProps {
  isOpen: boolean;
  activeThreadId: string | null;
  entries: RunLogEntry[];
  onClose: () => void;
}

function formatTime(timestamp: number): string {
  if (!timestamp) {
    return "Unknown time";
  }
  return new Date(timestamp).toLocaleString();
}

function badgeClass(kind: RunLogEntry["kind"]): string {
  if (kind === "run") {
    return "bg-blue-100 text-blue-700";
  }
  if (kind === "agent") {
    return "bg-emerald-100 text-emerald-700";
  }
  if (kind === "tool") {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-violet-100 text-violet-700";
}

export function RunLogDrawer({
  isOpen,
  activeThreadId,
  entries,
  onClose,
}: RunLogDrawerProps) {
  return (
    <aside
      className={`pointer-events-none fixed inset-y-0 right-0 z-50 w-full max-w-md transform border-l border-[var(--border-weak)] bg-[var(--bg-surface)] shadow-2xl transition-transform duration-200 ${
        isOpen ? "translate-x-0" : "translate-x-full"
      }`}
      aria-hidden={!isOpen}
    >
      <div className="pointer-events-auto flex h-full flex-col">
        <header className="flex items-center justify-between border-b border-[var(--border-weak)] px-4 py-3">
          <div>
            <p className="text-base font-bold">Run Log</p>
            <p className="text-xs text-[var(--text-secondary)]">
              Thread:{" "}
              <span className="font-mono-ui">
                {activeThreadId ?? "No active thread"}
              </span>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-[var(--border-weak)] px-2 py-1 text-xs font-semibold"
          >
            Close
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {entries.length === 0 ? (
            <div className="rounded-lg border border-dashed border-[var(--border-weak)] p-4 text-sm text-[var(--text-secondary)]">
              No run events yet for this thread.
            </div>
          ) : (
            <ul className="space-y-3">
              {entries.map((entry) => (
                <li
                  key={entry.id}
                  className="rounded-lg border border-[var(--border-weak)] bg-white p-3"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${badgeClass(entry.kind)}`}
                    >
                      {entry.kind}
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">
                      {formatTime(entry.createdAt)}
                    </span>
                  </div>
                  <p className="text-sm font-semibold">{entry.title}</p>
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">
                    {entry.description}
                  </p>
                  {entry.runId ? (
                    <p className="mt-2 text-[10px] text-[var(--text-secondary)]">
                      Run ID: <span className="font-mono-ui">{entry.runId}</span>
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </aside>
  );
}
