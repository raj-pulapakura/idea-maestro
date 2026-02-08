import {
  ChatRole,
  PersistedMessageRow,
  UiMessage,
} from "@/app/features/workspace/state/types";

export function getAgentInitials(name: string | null | undefined): string {
  if (!name) {
    return "AI";
  }
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function parseStoredContent(content: PersistedMessageRow["content"]): string {
  if (!content || typeof content !== "object") {
    return "";
  }

  if (typeof content.text === "string") {
    return content.text;
  }

  if (Array.isArray(content.blocks)) {
    const textBlocks = content.blocks
      .map((block) => {
        if (typeof block === "string") {
          return block;
        }
        if (block && typeof block === "object" && "text" in block) {
          const value = (block as { text?: unknown }).text;
          return typeof value === "string" ? value : "";
        }
        return "";
      })
      .filter(Boolean);
    return textBlocks.join("");
  }

  return "";
}

function mapStoredRole(role: string | undefined): ChatRole {
  if (role === "user" || role === "assistant" || role === "tool" || role === "system") {
    return role;
  }
  return "assistant";
}

export function mapHistoryRows(rows: PersistedMessageRow[]): UiMessage[] {
  return rows.map((row, index) => ({
    id: `history-${index}`,
    role: mapStoredRole(row.role),
    byAgent: row.by_agent ?? null,
    content: parseStoredContent(row.content),
    createdAt: index,
    isStreaming: false,
  }));
}
