"use client";

import { useCallback, useEffect, useMemo, useReducer } from "react";
import {
  fetchThreadMessages,
  postApprovalStream,
  postChatMessageStream,
} from "@/app/features/workspace/api/chat-client";
import { THREAD_STORAGE_KEY } from "@/app/features/workspace/constants";
import {
  chatReducer,
  createInitialChatState,
} from "@/app/features/workspace/state/reducer";
import { ChatState } from "@/app/features/workspace/state/types";
import { mapHistoryRows } from "@/app/features/workspace/utils/message-mappers";
import { buildThreadId } from "@/app/features/workspace/utils/thread-id";
import { buildTimeline } from "@/app/features/workspace/utils/timeline";

interface UseWorkspaceChatResult {
  state: ChatState;
  canSend: boolean;
  timeline: ReturnType<typeof buildTimeline>;
  setInput: (input: string) => void;
  sendMessage: (messageOverride?: string) => Promise<void>;
  submitApproval: (decision: "approve" | "reject") => Promise<void>;
}

export function useWorkspaceChat(): UseWorkspaceChatResult {
  const [state, dispatch] = useReducer(chatReducer, createInitialChatState(""));

  useEffect(() => {
    const stored = window.localStorage.getItem(THREAD_STORAGE_KEY);
    const threadId = stored || buildThreadId();
    if (!stored) {
      window.localStorage.setItem(THREAD_STORAGE_KEY, threadId);
    }
    dispatch({ type: "setThreadId", threadId });
  }, []);

  useEffect(() => {
    if (!state.threadId) {
      return;
    }

    let cancelled = false;
    fetchThreadMessages(state.threadId)
      .then((rows) => {
        if (cancelled) {
          return;
        }
        dispatch({ type: "hydrateMessages", messages: mapHistoryRows(rows) });
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
              : "Failed to load prior thread messages",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [state.threadId]);

  const timeline = useMemo(
    () => buildTimeline(state.messages, state.toolTimeline),
    [state.messages, state.toolTimeline],
  );

  const setInput = useCallback((input: string) => {
    dispatch({ type: "setInput", input });
  }, []);

  const sendMessage = useCallback(
    async (messageOverride?: string) => {
      const message = (messageOverride ?? state.input).trim();
      if (!message || !state.threadId || state.status === "streaming") {
        return;
      }

      dispatch({ type: "setInput", input: "" });
      dispatch({
        type: "pushUserMessage",
        message: {
          id: crypto.randomUUID(),
          role: "user",
          content: message,
          createdAt: Date.now(),
          isStreaming: false,
        },
      });
      dispatch({ type: "startStream" });

      try {
        await postChatMessageStream(state.threadId, message, (event) => {
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
    [state.input, state.status, state.threadId],
  );

  const submitApproval = useCallback(
    async (decision: "approve" | "reject") => {
      if (!state.threadId || state.status === "streaming") {
        return;
      }

      dispatch({ type: "startStream" });

      try {
        await postApprovalStream(state.threadId, decision, (event) => {
          dispatch({ type: "streamEvent", event });
        });
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
    [state.status, state.threadId],
  );

  return {
    state,
    canSend: state.input.trim().length > 0 && state.status !== "streaming",
    timeline,
    setInput,
    sendMessage,
    submitApproval,
  };
}
