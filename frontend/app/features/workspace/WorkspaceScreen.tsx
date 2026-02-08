"use client";

import { AppHeader } from "@/app/features/workspace/components/AppHeader";
import { ChatPanel } from "@/app/features/workspace/components/ChatPanel";
import { DocumentsPanel } from "@/app/features/workspace/components/DocumentsPanel";
import { SessionsPanel } from "@/app/features/workspace/components/SessionsPanel";
import { useWorkspaceChat } from "@/app/features/workspace/hooks/useWorkspaceChat";

export function WorkspaceScreen() {
  const { state, timeline, canSend, setInput, sendMessage, submitApproval } =
    useWorkspaceChat();

  return (
    <div className="h-screen overflow-hidden text-[var(--text-primary)]">
      <AppHeader />
      <main className="grid h-[calc(100vh-56px)] grid-cols-[280px_minmax(0,1fr)_360px]">
        <SessionsPanel />
        <ChatPanel
          state={state}
          timeline={timeline}
          canSend={canSend}
          onInputChange={setInput}
          onSend={sendMessage}
        />
        <DocumentsPanel
          pendingApproval={state.pendingApproval}
          status={state.status}
          onApproval={submitApproval}
        />
      </main>
    </div>
  );
}
