"use client";

import { useCallback, useEffect, useMemo, useReducer, useState } from "react";
import {
  createThread,
  fetchThreadChangesetDetail,
  fetchThreadChangesets,
  fetchThreadDoc,
  fetchThreadDocs,
  fetchThreads,
  fetchThreadSnapshot,
  postApprovalStream,
  postChatMessageStream,
} from "@/app/features/workspace/api/chat-client";
import { THREAD_STORAGE_KEY } from "@/app/features/workspace/constants";
import {
  createInitialWorkspaceState,
  getPendingApproval,
  workspaceReducer,
} from "@/app/features/workspace/state/reducer";
import {
  AgentStatusEntity,
  ChangeSetEntity,
  DocEntity,
  PendingApproval,
  RunEntity,
  ThreadEntity,
  WorkspaceState,
} from "@/app/features/workspace/state/types";
import { mapHistoryRows } from "@/app/features/workspace/utils/message-mappers";
import { buildRunLog, RunLogEntry } from "@/app/features/workspace/utils/run-log";
import { buildThreadId } from "@/app/features/workspace/utils/thread-id";
import { buildTimeline } from "@/app/features/workspace/utils/timeline";
import { useParams, useRouter } from "next/navigation";

interface UseWorkspaceChatResult {
  state: WorkspaceState;
  threads: ThreadEntity[];
  activeThreadId: string | null;
  docs: DocEntity[];
  activeDoc: DocEntity | null;
  changesets: ChangeSetEntity[];
  selectedChangeset: ChangeSetEntity | null;
  selectChangeset: (changeSetId: string) => void;
  pendingApproval: PendingApproval | null;
  latestRun: RunEntity | null;
  latestAgentStatuses: AgentStatusEntity[];
  isStreaming: boolean;
  canSend: boolean;
  timeline: ReturnType<typeof buildTimeline>;
  runLog: RunLogEntry[];
  setInput: (input: string) => void;
  selectThread: (threadId: string) => void;
  createNewThread: () => Promise<void>;
  selectDoc: (docId: string) => void;
  sendMessage: (messageOverride?: string) => Promise<void>;
  submitApproval: (
    decision: "approve" | "reject" | "request_changes",
    comment?: string | null,
    interruptId?: string | null,
  ) => Promise<void>;
}

export function useWorkspaceChat(): UseWorkspaceChatResult {
  const [state, dispatch] = useReducer(
    workspaceReducer,
    createInitialWorkspaceState(),
  );
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [selectedChangeSetId, setSelectedChangeSetId] = useState<string | null>(null);

  const router = useRouter();
  const params = useParams<{ threadId?: string }>();
  const threadFromRoute = typeof params?.threadId === "string" ? params.threadId : null;

  const updateUrlThread = useCallback(
    (threadId: string) => {
      router.replace(`/threads/${threadId}`);
    },
    [router],
  );

  const selectThread = useCallback(
    (threadId: string) => {
      if (state.streamStatus === "streaming" && threadId !== state.activeThreadId) {
        return;
      }
      dispatch({ type: "setActiveThread", threadId });
      updateUrlThread(threadId);
      window.localStorage.setItem(THREAD_STORAGE_KEY, threadId);
    },
    [state.activeThreadId, state.streamStatus, updateUrlThread],
  );

  const createNewThread = useCallback(async () => {
    if (state.streamStatus === "streaming") {
      return;
    }
    const thread = await createThread({ threadId: buildThreadId() });
    dispatch({ type: "hydrateThreads", threads: [thread] });
    selectThread(thread.thread_id);
  }, [selectThread, state.streamStatus]);

  useEffect(() => {
    if (!threadFromRoute) {
      return;
    }

    dispatch({ type: "setActiveThread", threadId: threadFromRoute });
    window.localStorage.setItem(THREAD_STORAGE_KEY, threadFromRoute);
  }, [threadFromRoute]);

  useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      try {
        const remoteThreads = await fetchThreads();
        if (cancelled) {
          return;
        }

        dispatch({ type: "hydrateThreads", threads: remoteThreads });

        if (threadFromRoute) {
          selectThread(threadFromRoute);
        }
      } catch (error: unknown) {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error:
            error instanceof Error ? error.message : "Failed to bootstrap threads",
        });
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [selectThread, threadFromRoute]);

  useEffect(() => {
    const threadId = state.activeThreadId;
    if (!threadId) {
      return;
    }

    let cancelled = false;
    fetchThreadSnapshot(threadId)
      .then((snapshot) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "hydrateSnapshot",
          threadId,
          snapshot,
          messages: mapHistoryRows(snapshot.messages),
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to load thread snapshot",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [state.activeThreadId]);

  useEffect(() => {
    const threadId = state.activeThreadId;
    if (!threadId) {
      return;
    }

    let cancelled = false;
    fetchThreadDocs(threadId)
      .then((docs) => {
        if (cancelled) {
          return;
        }

        dispatch({ type: "hydrateDocs", threadId, docs });
        setActiveDocId((current) => {
          if (current && docs.some((doc) => doc.doc_id === current)) {
            return current;
          }
          return docs[0]?.doc_id ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error: error instanceof Error ? error.message : "Failed to load docs",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [state.activeThreadId]);

  useEffect(() => {
    const threadId = state.activeThreadId;
    if (!threadId || !activeDocId) {
      return;
    }

    let cancelled = false;
    fetchThreadDoc(threadId, activeDocId)
      .then((doc) => {
        if (cancelled) {
          return;
        }
        dispatch({ type: "upsertDoc", doc });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to load document detail",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [activeDocId, state.activeThreadId]);

  useEffect(() => {
    const threadId = state.activeThreadId;
    if (!threadId) {
      return;
    }

    let cancelled = false;
    fetchThreadChangesets(threadId)
      .then((changesets) => {
        if (cancelled) {
          return;
        }

        dispatch({ type: "hydrateChangesets", threadId, changesets });
        setSelectedChangeSetId((current) => {
          if (current && changesets.some((changeset) => changeset.change_set_id === current)) {
            return current;
          }

          const pending = changesets.find((changeset) => changeset.status === "pending");
          return pending?.change_set_id ?? changesets[0]?.change_set_id ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to load changesets",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [state.activeThreadId]);

  useEffect(() => {
    const threadId = state.activeThreadId;
    if (!threadId || !selectedChangeSetId) {
      return;
    }

    let cancelled = false;
    fetchThreadChangesetDetail(threadId, selectedChangeSetId)
      .then((changeset) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "hydrateChangesets",
          threadId,
          changesets: [changeset],
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to load changeset detail",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [selectedChangeSetId, state.activeThreadId]);

  const threads = useMemo(
    () =>
      Object.values(state.threads).sort(
        (a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt),
      ),
    [state.threads],
  );

  const docs = useMemo(() => {
    if (!state.activeThreadId) {
      return [];
    }
    return Object.values(state.docs)
      .filter((doc) => doc.threadId === state.activeThreadId)
      .sort((a, b) => a.docId.localeCompare(b.docId));
  }, [state.activeThreadId, state.docs]);

  const activeDoc = useMemo(
    () => docs.find((doc) => doc.docId === activeDocId) ?? null,
    [activeDocId, docs],
  );

  const changesets = useMemo(() => {
    if (!state.activeThreadId) {
      return [];
    }

    return Object.values(state.changesets)
      .filter((changeset) => changeset.threadId === state.activeThreadId)
      .sort((a, b) => Date.parse(b.createdAt ?? "") - Date.parse(a.createdAt ?? ""));
  }, [state.activeThreadId, state.changesets]);

  const selectedChangeset = useMemo(
    () => changesets.find((changeset) => changeset.id === selectedChangeSetId) ?? null,
    [changesets, selectedChangeSetId],
  );

  const timeline = useMemo(() => {
    if (!state.activeThreadId) {
      return [];
    }

    const messages = state.messagesByThread[state.activeThreadId] ?? [];
    const activeRunIds = new Set(
      Object.values(state.runs)
        .filter((run) => run.threadId === state.activeThreadId)
        .map((run) => run.id),
    );

    const tools = Object.entries(state.toolTimelineByRun)
      .filter(([runId]) => activeRunIds.has(runId))
      .flatMap(([, items]) => items);

    return buildTimeline(messages, tools);
  }, [
    state.activeThreadId,
    state.messagesByThread,
    state.runs,
    state.toolTimelineByRun,
  ]);

  const pendingApproval = useMemo(
    () => getPendingApproval(state, state.activeThreadId),
    [state],
  );

  const runLog = useMemo(
    () =>
      buildRunLog({
        threadId: state.activeThreadId,
        runs: state.runs,
        agentStatuses: state.agentStatuses,
        toolTimelineByRun: state.toolTimelineByRun,
        changesets: state.changesets,
      }),
    [
      state.activeThreadId,
      state.runs,
      state.agentStatuses,
      state.toolTimelineByRun,
      state.changesets,
    ],
  );

  const latestRun = useMemo(() => {
    if (!state.activeThreadId) {
      return null;
    }
    const runs = Object.values(state.runs)
      .filter((run) => run.threadId === state.activeThreadId)
      .sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt));
    return runs[0] ?? null;
  }, [state.activeThreadId, state.runs]);

  const latestAgentStatuses = useMemo(() => {
    if (!latestRun) {
      return [];
    }
    return Object.values(state.agentStatuses)
      .filter((status) => status.runId === latestRun.id)
      .sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  }, [latestRun, state.agentStatuses]);

  const setInput = useCallback((input: string) => {
    dispatch({ type: "setInput", input });
  }, []);

  const selectDoc = useCallback((docId: string) => {
    setActiveDocId(docId);
  }, []);

  const selectChangeset = useCallback((changeSetId: string) => {
    setSelectedChangeSetId(changeSetId);
  }, []);

  const sendMessage = useCallback(
    async (messageOverride?: string) => {
      const message = (messageOverride ?? state.input).trim();
      if (!message || state.streamStatus === "streaming") {
        return;
      }

      let threadId = state.activeThreadId;
      if (!threadId) {
        const created = await createThread({ threadId: buildThreadId() });
        dispatch({ type: "hydrateThreads", threads: [created] });
        selectThread(created.thread_id);
        threadId = created.thread_id;
      }

      dispatch({ type: "setInput", input: "" });
      dispatch({
        type: "pushUserMessage",
        threadId,
        message: {
          id: crypto.randomUUID(),
          runId: null,
          role: "user",
          content: message,
          createdAt: Date.now(),
          isStreaming: false,
        },
      });
      dispatch({ type: "beginStream" });

      try {
        await postChatMessageStream(threadId, message, (event) => {
          dispatch({ type: "streamEvent", event });
        });
        dispatch({ type: "streamDone" });
      } catch (error: unknown) {
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to stream chat response",
        });
      }
    },
    [selectThread, state.activeThreadId, state.input, state.streamStatus],
  );

  const submitApproval = useCallback(
    async (
      decision: "approve" | "reject" | "request_changes",
      comment?: string | null,
      interruptId?: string | null,
    ) => {
      const threadId = state.activeThreadId;
      if (!threadId || state.streamStatus === "streaming") {
        return;
      }

      dispatch({ type: "beginStream" });

      try {
        await postApprovalStream(
          threadId,
          decision,
          comment ?? null,
          interruptId ?? null,
          (event) => {
            dispatch({ type: "streamEvent", event });
          },
        );
        const refreshedSnapshot = await fetchThreadSnapshot(threadId);
        dispatch({
          type: "hydrateSnapshot",
          threadId,
          snapshot: refreshedSnapshot,
          messages: mapHistoryRows(refreshedSnapshot.messages),
        });
        const refreshedChangesets = await fetchThreadChangesets(threadId);
        dispatch({
          type: "hydrateChangesets",
          threadId,
          changesets: refreshedChangesets,
        });
        if (selectedChangeSetId) {
          const refreshedDetail = await fetchThreadChangesetDetail(
            threadId,
            selectedChangeSetId,
          );
          dispatch({
            type: "hydrateChangesets",
            threadId,
            changesets: [refreshedDetail],
          });
        }
        dispatch({ type: "streamDone" });
      } catch (error: unknown) {
        dispatch({
          type: "streamError",
          error:
            error instanceof Error
              ? error.message
              : "Failed to submit approval decision",
        });
      }
    },
    [selectedChangeSetId, state.activeThreadId, state.streamStatus],
  );

  return {
    state,
    threads,
    activeThreadId: state.activeThreadId,
    docs,
    activeDoc,
    changesets,
    selectedChangeset,
    selectChangeset,
    pendingApproval,
    latestRun,
    latestAgentStatuses,
    isStreaming: state.streamStatus === "streaming",
    canSend: state.input.trim().length > 0 && state.streamStatus !== "streaming",
    timeline,
    runLog,
    setInput,
    selectThread,
    createNewThread,
    selectDoc,
    sendMessage,
    submitApproval,
  };
}
