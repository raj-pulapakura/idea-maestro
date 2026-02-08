import {
  DocEntity,
  PendingApproval,
  StreamStatus,
} from "@/app/features/workspace/state/types";

interface DocumentsPanelProps {
  docs: DocEntity[];
  activeDoc: DocEntity | null;
  pendingApproval: PendingApproval | null;
  status: StreamStatus;
  onToggleCollapse: () => void;
  onSelectDoc: (docId: string) => void;
  onApproval: (
    decision: "approve" | "reject" | "request_changes",
    comment?: string | null,
    interruptId?: string | null,
  ) => Promise<void>;
}

export function DocumentsPanel({
  docs,
  activeDoc,
  pendingApproval,
  status,
  onToggleCollapse,
  onSelectDoc,
  onApproval,
}: DocumentsPanelProps) {
  return (
    <aside className="app-scroll overflow-y-auto border-l border-[var(--border-weak)] bg-[var(--bg-panel)] p-4">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-bold uppercase tracking-wide">Living Documents</p>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-[var(--accent-soft)] px-2 py-1 text-xs font-semibold text-[var(--accent)]">
            Core
          </span>
          <button
            type="button"
            onClick={onToggleCollapse}
            className="rounded-md border border-[var(--border-weak)] bg-white px-2 py-1 text-xs font-semibold"
          >
            Collapse
          </button>
        </div>
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
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() =>
                void onApproval("approve", null, pendingApproval.interruptId ?? null)
              }
              disabled={status === "streaming"}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() =>
                void onApproval("reject", null, pendingApproval.interruptId ?? null)
              }
              disabled={status === "streaming"}
              className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Reject
            </button>
            <button
              type="button"
              onClick={() =>
                void onApproval(
                  "request_changes",
                  null,
                  pendingApproval.interruptId ?? null,
                )
              }
              disabled={status === "streaming"}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Request Changes
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-2">
        {docs.map((doc) => {
          const isActive = activeDoc?.docId === doc.docId;
          return (
            <div
              key={doc.id}
              className={`rounded-xl border bg-white ${
                isActive
                  ? "border-[var(--accent)]"
                  : "border-[var(--border-weak)]"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelectDoc(doc.docId)}
                className="w-full p-3 text-left"
              >
                <p className="text-sm font-bold">{doc.title}</p>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">
                  v{doc.version} • {doc.updatedBy || "System"}
                </p>
              </button>
              {isActive ? (
                <div className="border-t border-[var(--border-weak)] px-3 pb-3">
                  <p className="mt-2 text-xs text-[var(--text-secondary)]">
                    {doc.description}
                  </p>
                  <div className="mt-2 max-h-56 overflow-y-auto rounded-md bg-[var(--bg-muted)] p-2">
                    <pre className="whitespace-pre-wrap text-xs leading-5">
                      {doc.content || "No content yet"}
                    </pre>
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
