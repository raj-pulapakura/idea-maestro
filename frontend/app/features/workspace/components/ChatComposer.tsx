interface ChatComposerProps {
  input: string;
  canSend: boolean;
  onInputChange: (value: string) => void;
  onSend: () => Promise<void>;
}

export function ChatComposer({
  input,
  canSend,
  onInputChange,
  onSend,
}: ChatComposerProps) {
  return (
    <div className="border-t border-[var(--border-weak)] bg-[var(--bg-surface)] px-6 py-4">
      <div className="rounded-2xl border border-[var(--border-weak)] bg-white p-3 shadow-[0_4px_18px_rgba(20,45,90,0.06)]">
        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
              event.preventDefault();
              void onSend();
            }
          }}
          placeholder="Message your agents. Use @ and # in Phase 2."
          className="h-24 w-full resize-none bg-transparent text-sm outline-none"
        />
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-[var(--text-secondary)]">Cmd/Ctrl + Enter to send</p>
          <button
            type="button"
            onClick={() => void onSend()}
            disabled={!canSend}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
