import { StreamEvent, ThreadSnapshot } from "@/app/features/workspace/state/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

interface ParsedSseChunk {
  eventType: string;
  data: unknown;
}

const STREAM_READ_TIMEOUT_MS = 120000;

function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function parseEventChunk(chunk: string): ParsedSseChunk | null {
  const lines = chunk.split("\n");
  let eventType = "message";
  const dataLines: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  const dataText = dataLines.join("\n");
  try {
    return { eventType, data: JSON.parse(dataText) };
  } catch {
    return { eventType, data: { raw: dataText } };
  }
}

async function streamSseResponse(
  response: Response,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body is missing");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const readWithTimeout = () =>
    new Promise<ReadableStreamReadResult<Uint8Array>>((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(
          new Error(
            "Stream timed out after 120s without updates. Please retry this request.",
          ),
        );
      }, STREAM_READ_TIMEOUT_MS);

      reader
        .read()
        .then((result) => {
          clearTimeout(timeoutId);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
    });

  while (true) {
    const { done, value } = await readWithTimeout();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const parsed = parseEventChunk(chunk);
      if (!parsed) {
        continue;
      }
      onEvent({ type: parsed.eventType, data: parsed.data });
    }
  }
}

export async function postChatMessageStream(
  threadId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(buildApiUrl(`/api/chat/${threadId}`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, client_message_id: crypto.randomUUID() }),
  });

  await streamSseResponse(response, onEvent);
}

export async function postApprovalStream(
  threadId: string,
  decision: "approve" | "reject" | "request_changes",
  comment: string | null,
  interruptId: string | null,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(buildApiUrl(`/api/chat/${threadId}/approval`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      decision,
      comment,
      interrupt_id: interruptId,
    }),
  });

  await streamSseResponse(response, onEvent);
}

export async function fetchThreadSnapshot(threadId: string): Promise<ThreadSnapshot> {
  const response = await fetch(buildApiUrl(`/api/chat/${threadId}`));
  if (!response.ok) {
    throw new Error(`Failed to load thread ${threadId}`);
  }

  const payload = (await response.json()) as {
    thread?: ThreadSnapshot["thread"];
    messages?: ThreadSnapshot["messages"];
    docs?: ThreadSnapshot["docs"];
    runs?: ThreadSnapshot["runs"];
    agent_statuses?: ThreadSnapshot["agent_statuses"];
    changesets?: ThreadSnapshot["changesets"];
  };

  return {
    thread: payload.thread ?? null,
    messages: payload.messages ?? [],
    docs: payload.docs ?? [],
    runs: payload.runs ?? [],
    agent_statuses: payload.agent_statuses ?? [],
    changesets: payload.changesets ?? [],
  };
}

export async function fetchThreads(): Promise<
  NonNullable<ThreadSnapshot["thread"]>[]
> {
  const response = await fetch(buildApiUrl("/api/threads"));
  if (!response.ok) {
    throw new Error("Failed to load threads");
  }

  const payload = (await response.json()) as {
    threads?: ThreadSnapshot["thread"][];
  };
  return (payload.threads ?? []).filter(
    (thread): thread is NonNullable<ThreadSnapshot["thread"]> => thread !== null,
  );
}

export async function createThread(params?: {
  title?: string;
  threadId?: string;
}): Promise<NonNullable<ThreadSnapshot["thread"]>> {
  const response = await fetch(buildApiUrl("/api/threads"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: params?.title,
      thread_id: params?.threadId,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to create thread: ${body}`);
  }

  const payload = (await response.json()) as {
    thread?: ThreadSnapshot["thread"];
  };
  if (!payload.thread) {
    throw new Error("Thread was not returned from create API");
  }
  return payload.thread;
}

export async function fetchThreadDocs(threadId: string): Promise<ThreadSnapshot["docs"]> {
  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/docs`));
  if (!response.ok) {
    throw new Error(`Failed to load docs for thread ${threadId}`);
  }

  const payload = (await response.json()) as {
    docs?: ThreadSnapshot["docs"];
  };
  return payload.docs ?? [];
}

export async function fetchThreadDoc(
  threadId: string,
  docId: string,
): Promise<ThreadSnapshot["docs"][number]> {
  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/docs/${docId}`));
  if (!response.ok) {
    throw new Error(`Failed to load doc ${docId}`);
  }

  const payload = (await response.json()) as {
    doc?: ThreadSnapshot["docs"][number];
  };
  if (!payload.doc) {
    throw new Error(`Doc ${docId} not found`);
  }
  return payload.doc;
}

export async function fetchThreadChangesets(
  threadId: string,
): Promise<ThreadSnapshot["changesets"]> {
  const response = await fetch(buildApiUrl(`/api/threads/${threadId}/changesets`));
  if (!response.ok) {
    throw new Error(`Failed to load changesets for thread ${threadId}`);
  }

  const payload = (await response.json()) as {
    changesets?: ThreadSnapshot["changesets"];
  };
  return payload.changesets ?? [];
}

export async function fetchThreadChangesetDetail(
  threadId: string,
  changeSetId: string,
): Promise<ThreadSnapshot["changesets"][number]> {
  const response = await fetch(
    buildApiUrl(`/api/threads/${threadId}/changesets/${changeSetId}`),
  );
  if (!response.ok) {
    throw new Error(`Failed to load changeset ${changeSetId}`);
  }

  const payload = (await response.json()) as {
    changeset?: ThreadSnapshot["changesets"][number];
  };
  if (!payload.changeset) {
    throw new Error(`Changeset ${changeSetId} not found`);
  }
  return payload.changeset;
}
