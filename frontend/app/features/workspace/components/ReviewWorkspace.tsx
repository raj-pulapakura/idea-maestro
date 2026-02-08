"use client";

import { useMemo, useState } from "react";

import { AGENT_COLOR } from "@/app/features/workspace/constants";
import {
  AgentStatusEntity,
  ChangeSetEntity,
  RunEntity,
  StreamStatus,
} from "@/app/features/workspace/state/types";
import { getAgentInitials } from "@/app/features/workspace/utils/message-mappers";
import { TimelineEntry } from "@/app/features/workspace/utils/timeline";

interface ReviewWorkspaceProps {
  timeline: TimelineEntry[];
  changesets: ChangeSetEntity[];
  selectedChangeset: ChangeSetEntity | null;
  status: StreamStatus;
  latestRun: RunEntity | null;
  latestAgentStatuses: AgentStatusEntity[];
  onSelectChangeset: (changeSetId: string) => void;
  onBackToChat: () => void;
  onApproval: (
    decision: "approve" | "reject" | "request_changes",
    comment?: string | null,
    interruptId?: string | null,
  ) => Promise<void>;
}

function countDiffStats(diff: string): { additions: number; deletions: number } {
  let additions = 0;
  let deletions = 0;

  for (const line of diff.split("\n")) {
    if (line.startsWith("+++") || line.startsWith("---")) {
      continue;
    }
    if (line.startsWith("+")) {
      additions += 1;
    } else if (line.startsWith("-")) {
      deletions += 1;
    }
  }

  return { additions, deletions };
}

export function ReviewWorkspace({
  timeline,
  changesets,
  selectedChangeset,
  status,
  latestRun,
  latestAgentStatuses,
  onSelectChangeset,
  onBackToChat,
  onApproval,
}: ReviewWorkspaceProps) {
  const defaultDocId =
    selectedChangeset?.docChanges[0]?.docId ?? selectedChangeset?.docs[0] ?? null;
  const [viewMode, setViewMode] = useState<"side-by-side" | "unified">("side-by-side");
  const [activeDocId, setActiveDocId] = useState<string | null>(defaultDocId);
  const [comment, setComment] = useState(selectedChangeset?.decisionNote ?? "");
  const [approvedDocIds, setApprovedDocIds] = useState<string[]>([]);

  const activeDocChange = useMemo(() => {
    if (!selectedChangeset) {
      return null;
    }

    if (!activeDocId) {
      return selectedChangeset.docChanges[0] ?? null;
    }

    return (
      selectedChangeset.docChanges.find((docChange) => docChange.docId === activeDocId) ??
      selectedChangeset.docChanges[0] ??
      null
    );
  }, [activeDocId, selectedChangeset]);

  const diffStats = useMemo(
    () => countDiffStats(activeDocChange?.diff ?? ""),
    [activeDocChange],
  );

  const reviewDocIds = useMemo(() => {
    if (!selectedChangeset) {
      return [];
    }
    const fromDocChanges = selectedChangeset.docChanges.map((docChange) => docChange.docId);
    if (fromDocChanges.length > 0) {
      return fromDocChanges;
    }
    return selectedChangeset.docs;
  }, [selectedChangeset]);

  const pendingDocIds = useMemo(
    () => reviewDocIds.filter((docId) => !approvedDocIds.includes(docId)),
    [approvedDocIds, reviewDocIds],
  );
  const currentDocId = activeDocId ?? reviewDocIds[0] ?? null;
  const isCurrentDocApproved =
    !!currentDocId && approvedDocIds.includes(currentDocId);

  const approvalDisabled =
    status === "streaming" ||
    !selectedChangeset ||
    selectedChangeset.status !== "pending" ||
    isCurrentDocApproved;

  const handleApprove = async () => {
    if (approvalDisabled || !selectedChangeset) {
      return;
    }

    if (currentDocId) {
      const nextPendingDocId = pendingDocIds.find((docId) => docId !== currentDocId);
      if (nextPendingDocId) {
        setApprovedDocIds((prev) =>
          prev.includes(currentDocId) ? prev : [...prev, currentDocId],
        );
        setActiveDocId(nextPendingDocId);
        return;
      }
    }

    await onApproval("approve", comment, selectedChangeset.interruptId ?? null);
  };

  return (
    <section className="flex h-full min-h-0 min-w-0 flex-col overflow-hidden bg-[var(--bg-surface)]">
      <header className="border-b border-[var(--border-weak)] px-6 py-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xl font-bold">Review Workspace</p>
          <button
            type="button"
            onClick={onBackToChat}
            className="rounded-lg border border-[var(--border-weak)] bg-white px-3 py-1.5 text-xs font-semibold"
          >
            Back to Chat
          </button>
        </div>
        <p className="text-xs text-[var(--text-secondary)]">
          Diff queue and approval history
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

      <div className="grid min-h-0 flex-1 grid-cols-[320px_minmax(0,1fr)] overflow-hidden">
        <aside className="app-scroll overflow-y-auto border-r border-[var(--border-weak)] bg-[var(--bg-panel)] p-4">
          <p className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--text-secondary)]">
            Change Queue
          </p>
          <div className="space-y-2">
            {changesets.map((changeset) => {
              const isActive = changeset.id === selectedChangeset?.id;
              return (
                <button
                  key={changeset.id}
                  type="button"
                  onClick={() => onSelectChangeset(changeset.id)}
                  className={`w-full rounded-xl border p-3 text-left ${
                    isActive
                      ? "border-[var(--accent)] bg-white"
                      : "border-[var(--border-weak)] bg-white"
                  }`}
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold">{changeset.summary || "Untitled changes"}</p>
                    <span className="rounded-full bg-[var(--bg-muted)] px-2 py-0.5 text-[10px] font-semibold uppercase">
                      {changeset.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {changeset.createdBy} · {changeset.docs.length} doc(s)
                  </p>
                </button>
              );
            })}
          </div>

          <div className="mt-5 border-t border-[var(--border-weak)] pt-4">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--text-secondary)]">
              Project Feed
            </p>
            <div className="space-y-3">
              {timeline.map((entry) => {
                if (entry.kind === "tool") {
                  return (
                    <div
                      key={entry.id}
                      className="rounded-lg border border-[var(--border-weak)] bg-[var(--bg-muted)] p-3"
                    >
                      <p className="text-xs font-semibold">{entry.tool.label}</p>
                      <p className="mt-1 text-[11px] text-[var(--text-secondary)]">
                        {entry.tool.byAgent || "agent activity"}
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
                  <div key={entry.id} className="flex items-start gap-2">
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[10px] font-bold text-white ${avatarColor}`}
                    >
                      {isUser ? "YU" : getAgentInitials(message.byAgent)}
                    </div>
                    <div className="rounded-lg border border-[var(--border-weak)] bg-white px-2.5 py-2 text-xs">
                      <p className="mb-1 text-[10px] font-semibold text-[var(--text-secondary)]">
                        {isUser ? "You" : message.byAgent || "Agent"}
                      </p>
                      <p className="line-clamp-3 whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-5 border-t border-[var(--border-weak)] pt-4">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--text-secondary)]">
              Review History
            </p>
            <div className="space-y-2">
              {(selectedChangeset?.reviews ?? []).length === 0 ? (
                <p className="text-xs text-[var(--text-secondary)]">No reviews yet.</p>
              ) : null}
              {(selectedChangeset?.reviews ?? []).map((review, index) => (
                <div
                  key={`${review.reviewedAt}-${index}`}
                  className="rounded-lg border border-[var(--border-weak)] bg-white p-2.5"
                >
                  <p className="text-[11px] font-semibold uppercase">
                    {review.decision.replace("_", " ")}
                  </p>
                  <p className="mt-1 text-[11px] text-[var(--text-secondary)]">
                    {review.comment || "No comment"}
                  </p>
                  <p className="mt-1 text-[10px] text-[var(--text-secondary)]">
                    {review.reviewedBy || "user"}{" "}
                    {review.reviewedAt
                      ? `· ${new Date(review.reviewedAt).toLocaleString()}`
                      : ""}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <div className="flex min-h-0 flex-col">
          <div className="flex items-center justify-between border-b border-[var(--border-weak)] px-6 py-3">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-bold">{activeDocChange?.docId || "Select a changeset"}</h3>
              <div className="rounded-lg bg-[var(--bg-muted)] p-1">
                <button
                  type="button"
                  onClick={() => setViewMode("side-by-side")}
                  className={`rounded px-2 py-1 text-xs font-semibold ${
                    viewMode === "side-by-side"
                      ? "bg-white"
                      : "text-[var(--text-secondary)]"
                  }`}
                >
                  Side-by-Side
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("unified")}
                  className={`rounded px-2 py-1 text-xs font-semibold ${
                    viewMode === "unified" ? "bg-white" : "text-[var(--text-secondary)]"
                  }`}
                >
                  Unified
                </button>
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs text-[var(--text-secondary)]">
              <span>+{diffStats.additions}</span>
              <span>-{diffStats.deletions}</span>
            </div>
          </div>

          <div className="border-b border-[var(--border-weak)] px-6 py-2">
            <div className="flex flex-wrap gap-2">
              {(selectedChangeset?.docChanges ?? []).map((docChange) => (
                <button
                  key={docChange.docId}
                  type="button"
                  onClick={() => setActiveDocId(docChange.docId)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    activeDocId === docChange.docId
                      ? "bg-[var(--accent)] text-white"
                      : approvedDocIds.includes(docChange.docId)
                        ? "bg-emerald-100 text-emerald-800"
                      : "bg-[var(--bg-muted)] text-[var(--text-secondary)]"
                  }`}
                >
                  {docChange.docId}
                  {approvedDocIds.includes(docChange.docId) ? " · Approved" : ""}
                </button>
              ))}
            </div>
          </div>

          <div className="app-scroll min-h-0 flex-1 overflow-y-auto px-6 py-4">
            {!activeDocChange ? (
              <p className="text-sm text-[var(--text-secondary)]">No diff selected.</p>
            ) : null}

            {activeDocChange && viewMode === "side-by-side" ? (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-4">
                  <p className="mb-3 text-xs font-bold uppercase tracking-wide text-rose-700">
                    Before
                  </p>
                  <pre className="whitespace-pre-wrap text-xs leading-5">
                    {activeDocChange.beforeContent || "(empty)"}
                  </pre>
                </div>
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4">
                  <p className="mb-3 text-xs font-bold uppercase tracking-wide text-emerald-700">
                    After
                  </p>
                  <pre className="whitespace-pre-wrap text-xs leading-5">
                    {activeDocChange.afterContent || "(empty)"}
                  </pre>
                </div>
              </div>
            ) : null}

            {activeDocChange && viewMode === "unified" ? (
              <div className="rounded-xl border border-[var(--border-weak)] bg-white p-4">
                <pre className="whitespace-pre-wrap text-xs leading-5">
                  {activeDocChange.diff.split("\n").map((line, index) => {
                    const className = line.startsWith("+") && !line.startsWith("+++")
                      ? "bg-emerald-100"
                      : line.startsWith("-") && !line.startsWith("---")
                        ? "bg-rose-100"
                        : "";
                    return (
                      <div key={`${line}-${index}`} className={className}>
                        {line || " "}
                      </div>
                    );
                  })}
                </pre>
              </div>
            ) : null}
          </div>

          <footer className="border-t border-[var(--border-weak)] bg-white px-6 py-4">
            <div className="mb-3">
              <label className="mb-1 block text-xs font-semibold text-[var(--text-secondary)]">
                Review comment (optional)
              </label>
              <textarea
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                rows={2}
                className="w-full rounded-lg border border-[var(--border-weak)] px-3 py-2 text-sm outline-none"
                placeholder="Add context for approve/reject/request changes"
              />
              <p className="mt-2 text-xs text-[var(--text-secondary)]">
                Reviewed {approvedDocIds.length} of {reviewDocIds.length} doc(s)
                {isCurrentDocApproved ? " · Current doc already approved" : ""}
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                onClick={() =>
                  void onApproval(
                    "request_changes",
                    comment,
                    selectedChangeset?.interruptId ?? null,
                  )
                }
                disabled={approvalDisabled}
                className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 disabled:opacity-50"
              >
                Request Changes
              </button>
              <button
                type="button"
                onClick={() =>
                  void onApproval(
                    "reject",
                    comment,
                    selectedChangeset?.interruptId ?? null,
                  )
                }
                disabled={approvalDisabled}
                className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50"
              >
                Reject
              </button>
              <button
                type="button"
                onClick={() => void handleApprove()}
                disabled={approvalDisabled}
                className="rounded-lg bg-[var(--accent)] px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {pendingDocIds.length > 1 ? "Approve & Next Doc" : "Approve"}
              </button>
            </div>
          </footer>
        </div>
      </div>
    </section>
  );
}
