import { PendingApproval, StreamStatus } from "@/app/features/workspace/state/types";

interface DocumentsPanelProps {
  pendingApproval: PendingApproval | null;
  status: StreamStatus;
  onApproval: (decision: "approve" | "reject") => Promise<void>;
}

export function DocumentsPanel({
  pendingApproval,
  status,
  onApproval,
}: DocumentsPanelProps) {
  return (
    <aside className="app-scroll overflow-y-auto border-l border-[var(--border-weak)] bg-[var(--bg-panel)] p-4">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-bold uppercase tracking-wide">Living Documents</p>
        <span className="rounded-full bg-[var(--accent-soft)] px-2 py-1 text-xs font-semibold text-[var(--accent)]">
          Core
        </span>
      </div>

      {pendingApproval ? (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
          <p className="text-sm font-bold text-amber-900">Approval Required</p>
          <p className="mt-1 text-sm text-amber-900">{pendingApproval.summary}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {pendingApproval.docs.map((doc) => (
              <span
                key={doc}
                className="rounded-md bg-amber-100 px-2 py-1 text-xs font-medium text-amber-900"
              >
                {doc}
              </span>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={() => void onApproval("approve")}
              disabled={status === "streaming"}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => void onApproval("reject")}
              disabled={status === "streaming"}
              className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-3">
        <div className="rounded-xl border border-[var(--border-weak)] bg-white p-4">
          <p className="text-sm font-bold">The Pitch (v7)</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Current Draft</p>
        </div>
        <div className="rounded-xl border border-[var(--border-weak)] bg-white p-4">
          <p className="text-sm font-bold">Risk Register (v4)</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Recently updated</p>
        </div>
        <div className="rounded-xl border border-[var(--border-weak)] bg-white p-4">
          <p className="text-sm font-bold">Technical Spec</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Initial draft</p>
        </div>
      </div>
    </aside>
  );
}
