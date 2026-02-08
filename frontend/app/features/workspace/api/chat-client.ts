import {
  PersistedMessageRow,
  StreamEvent,
} from "@/app/features/workspace/state/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

interface ParsedSseChunk {
  eventType: string;
  data: unknown;
}

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

  while (true) {
    const { done, value } = await reader.read();
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
  decision: "approve" | "reject",
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(buildApiUrl(`/api/chat/${threadId}/approval`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ decision }),
  });

  await streamSseResponse(response, onEvent);
}

export async function fetchThreadMessages(
  threadId: string,
): Promise<PersistedMessageRow[]> {
  const response = await fetch(buildApiUrl(`/api/chat/${threadId}`));
  if (!response.ok) {
    throw new Error(`Failed to load thread ${threadId}`);
  }
  const payload = (await response.json()) as {
    messages?: PersistedMessageRow[];
  };
  return payload.messages ?? [];
}
