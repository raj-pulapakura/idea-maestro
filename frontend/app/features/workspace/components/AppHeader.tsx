interface AppHeaderProps {
  onOpenRunLog: () => void;
}

export function AppHeader({ onOpenRunLog }: AppHeaderProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--border-weak)] bg-[var(--bg-surface)] px-5">
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] font-mono-ui text-sm text-white">
            IM
          </div>
          <p className="text-base font-extrabold">Idea Maestro</p>
        </div>
        <p className="text-sm text-[var(--text-secondary)]">
          Project:{" "}
          <span className="font-semibold text-[var(--text-primary)]">
            NextGen SaaS
          </span>
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenRunLog}
          className="rounded-lg border border-[var(--border-weak)] bg-[var(--bg-surface)] px-3 py-1.5 text-sm font-semibold"
        >
          Run Log
        </button>
        <button
          type="button"
          className="rounded-lg bg-[var(--accent-soft)] px-3 py-1.5 text-sm font-semibold text-[var(--accent)]"
        >
          Pause Agents
        </button>
        <button
          type="button"
          className="rounded-lg border border-[var(--border-weak)] bg-[var(--bg-surface)] px-3 py-1.5 text-sm font-semibold"
        >
          Settings
        </button>
      </div>
    </header>
  );
}
