import {
  ToolTimelineItem,
  UiMessage,
} from "@/app/features/workspace/state/types";

export type TimelineEntry =
  | {
      kind: "message";
      id: string;
      createdAt: number;
      message: UiMessage;
    }
  | {
      kind: "tool";
      id: string;
      createdAt: number;
      tool: ToolTimelineItem;
    };

export function buildTimeline(
  messages: UiMessage[],
  toolTimeline: ToolTimelineItem[],
): TimelineEntry[] {
  const messageItems: TimelineEntry[] = messages.map((message) => ({
    kind: "message",
    createdAt: message.createdAt,
    id: `m-${message.id}`,
    message,
  }));

  const toolItems: TimelineEntry[] = toolTimeline.map((tool) => ({
    kind: "tool",
    createdAt: tool.createdAt,
    id: `t-${tool.id}`,
    tool,
  }));

  return [...messageItems, ...toolItems].sort((a, b) => {
    if (a.createdAt !== b.createdAt) {
      return a.createdAt - b.createdAt;
    }
    return a.id.localeCompare(b.id);
  });
}
