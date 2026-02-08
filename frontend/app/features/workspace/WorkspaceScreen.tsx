"use client";

import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/app/features/workspace/components/AppHeader";
import { ChatPanel } from "@/app/features/workspace/components/ChatPanel";
import { DocumentsPanel } from "@/app/features/workspace/components/DocumentsPanel";
import { ReviewWorkspace } from "@/app/features/workspace/components/ReviewWorkspace";
import { RunLogDrawer } from "@/app/features/workspace/components/RunLogDrawer";
import { SessionsPanel } from "@/app/features/workspace/components/SessionsPanel";
import { PANEL_PREFS_STORAGE_KEY } from "@/app/features/workspace/constants";
import { useWorkspaceChat } from "@/app/features/workspace/hooks/useWorkspaceChat";

interface PanelPrefs {
  sessionsCollapsed: boolean;
  docsCollapsed: boolean;
}

function getInitialPanelPrefs(): PanelPrefs {
  if (typeof window === "undefined") {
    return { sessionsCollapsed: false, docsCollapsed: false };
  }

  const raw = window.localStorage.getItem(PANEL_PREFS_STORAGE_KEY);
  if (!raw) {
    return { sessionsCollapsed: false, docsCollapsed: false };
  }

  try {
    const parsed = JSON.parse(raw) as Partial<PanelPrefs>;
    return {
      sessionsCollapsed: Boolean(parsed.sessionsCollapsed),
      docsCollapsed: Boolean(parsed.docsCollapsed),
    };
  } catch {
    return { sessionsCollapsed: false, docsCollapsed: false };
  }
}

export function WorkspaceScreen() {
  const [isRunLogOpen, setIsRunLogOpen] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState<"chat" | "review">("chat");
  const [reviewManuallyClosed, setReviewManuallyClosed] = useState(false);
  const [panelPrefs, setPanelPrefs] = useState<PanelPrefs>(getInitialPanelPrefs);
  const { sessionsCollapsed: isSessionsCollapsed, docsCollapsed: isDocsCollapsed } =
    panelPrefs;
  const {
    state,
    threads,
    activeThreadId,
    docs,
    activeDoc,
    changesets,
    selectedChangeset,
    selectChangeset,
    pendingApproval,
    latestRun,
    latestAgentStatuses,
    isStreaming,
    timeline,
    runLog,
    canSend,
    setInput,
    selectThread,
    createNewThread,
    selectDoc,
    sendMessage,
    submitApproval,
  } = useWorkspaceChat();

  useEffect(() => {
    const prefs: PanelPrefs = {
      sessionsCollapsed: isSessionsCollapsed,
      docsCollapsed: isDocsCollapsed,
    };
    window.localStorage.setItem(PANEL_PREFS_STORAGE_KEY, JSON.stringify(prefs));
  }, [isDocsCollapsed, isSessionsCollapsed]);

  const hasPendingChangesets = changesets.some(
    (changeset) => changeset.status === "pending",
  );
  const hasAnyChangesets = changesets.length > 0;
  const isReviewMode =
    hasAnyChangesets &&
    (workspaceMode === "review" || (hasPendingChangesets && !reviewManuallyClosed));

  const handleApproval = async (
    decision: "approve" | "reject" | "request_changes",
    comment?: string | null,
    interruptId?: string | null,
  ) => {
    await submitApproval(decision, comment, interruptId);
    setReviewManuallyClosed(false);
    setWorkspaceMode("chat");
  };

  const handleSend = async () => {
    setReviewManuallyClosed(false);
    await sendMessage();
  };

  const gridColumns = useMemo(() => {
    if (isReviewMode) {
      return isSessionsCollapsed
        ? "56px minmax(0,1fr)"
        : "280px minmax(0,1fr)";
    }
    return `${isSessionsCollapsed ? "56px" : "280px"} minmax(0,1fr) ${isDocsCollapsed ? "56px" : "360px"}`;
  }, [isDocsCollapsed, isReviewMode, isSessionsCollapsed]);

  return (
    <div className="h-screen overflow-hidden text-[var(--text-primary)]">
      <AppHeader onOpenRunLog={() => setIsRunLogOpen(true)} />
      <main
        className="grid h-[calc(100vh-56px)]"
        style={{ gridTemplateColumns: gridColumns }}
      >
        {isSessionsCollapsed ? (
          <aside className="flex flex-col items-center gap-2 border-r border-[var(--border-weak)] bg-[var(--bg-panel)] px-2 py-3">
            <button
              type="button"
              onClick={() =>
                setPanelPrefs((prev) => ({ ...prev, sessionsCollapsed: false }))
              }
              className="w-full rounded-md border border-[var(--border-weak)] bg-white px-1 py-2 text-[10px] font-semibold"
              title="Expand Sessions"
            >
              &gt;
            </button>
            <button
              type="button"
              disabled={isStreaming}
              onClick={() => void createNewThread()}
              className="w-full rounded-md bg-[var(--accent)] px-1 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
              title="New Session"
            >
              +
            </button>
          </aside>
        ) : (
          <SessionsPanel
            threads={threads}
            activeThreadId={activeThreadId}
            isStreaming={isStreaming}
            onToggleCollapse={() =>
              setPanelPrefs((prev) => ({ ...prev, sessionsCollapsed: true }))
            }
            onSelectThread={selectThread}
            onCreateThread={createNewThread}
          />
        )}
        {isReviewMode ? (
          <div className="min-h-0 min-w-0">
            <ReviewWorkspace
              key={`${selectedChangeset?.id ?? "review-none"}:${selectedChangeset?.decidedAt ?? ""}`}
              timeline={timeline}
              changesets={changesets}
              selectedChangeset={selectedChangeset}
              status={state.streamStatus}
              latestRun={latestRun}
              latestAgentStatuses={latestAgentStatuses}
              onSelectChangeset={selectChangeset}
              onBackToChat={() => {
                setReviewManuallyClosed(true);
                setWorkspaceMode("chat");
              }}
              onApproval={handleApproval}
            />
          </div>
        ) : (
          <>
            <ChatPanel
              state={state}
              activeThreadId={activeThreadId}
              latestRun={latestRun}
              latestAgentStatuses={latestAgentStatuses}
              timeline={timeline}
              canSend={canSend}
              onInputChange={setInput}
              onSend={handleSend}
            />
            {isDocsCollapsed ? (
              <aside className="flex flex-col items-center gap-2 border-l border-[var(--border-weak)] bg-[var(--bg-panel)] px-2 py-3">
                <button
                  type="button"
                  onClick={() =>
                    setPanelPrefs((prev) => ({ ...prev, docsCollapsed: false }))
                  }
                  className="w-full rounded-md border border-[var(--border-weak)] bg-white px-1 py-2 text-[10px] font-semibold"
                  title="Expand Documents"
                >
                  &lt;
                </button>
                <p className="text-[10px] font-semibold uppercase text-[var(--text-secondary)]">
                  Docs
                </p>
              </aside>
            ) : (
              <DocumentsPanel
                docs={docs}
                activeDoc={activeDoc}
                pendingApproval={pendingApproval}
                status={state.streamStatus}
                onToggleCollapse={() =>
                  setPanelPrefs((prev) => ({ ...prev, docsCollapsed: true }))
                }
                onSelectDoc={selectDoc}
                onApproval={submitApproval}
              />
            )}
          </>
        )}
      </main>
      <RunLogDrawer
        isOpen={isRunLogOpen}
        activeThreadId={activeThreadId}
        entries={runLog}
        onClose={() => setIsRunLogOpen(false)}
      />
    </div>
  );
}
