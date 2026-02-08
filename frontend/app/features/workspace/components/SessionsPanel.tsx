export function SessionsPanel() {
  return (
    <aside className="app-scroll overflow-y-auto border-r border-[var(--border-weak)] bg-[var(--bg-panel)] p-3">
      <button
        type="button"
        className="mb-3 w-full rounded-xl bg-[var(--accent)] px-4 py-3 text-sm font-bold text-white"
      >
        + New Session
      </button>
      <input
        placeholder="Search sessions..."
        className="mb-4 w-full rounded-xl border border-[var(--border-weak)] bg-white px-3 py-2 text-sm outline-none"
      />
      <p className="mb-2 text-xs font-bold uppercase tracking-wide text-[var(--text-secondary)]">
        Active Workspaces
      </p>
      <div className="space-y-2">
        <div className="rounded-xl border border-[var(--border-weak)] bg-white p-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Solo Founder AI PM</p>
            <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
          </div>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Drafting Pitch</p>
        </div>
        <div className="rounded-xl border border-transparent bg-[var(--bg-muted)] p-3">
          <p className="text-sm font-semibold">E-commerce Engine</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Technical Spec</p>
        </div>
      </div>
    </aside>
  );
}
