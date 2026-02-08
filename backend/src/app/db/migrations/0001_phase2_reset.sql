DROP TABLE IF EXISTS change_set_reviews CASCADE;
DROP TABLE IF EXISTS change_set_docs CASCADE;
DROP TABLE IF EXISTS change_sets CASCADE;
DROP TABLE IF EXISTS agent_status_events CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS doc_versions CASCADE;
DROP TABLE IF EXISTS docs CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_threads CASCADE;

-- Reset LangGraph checkpoint state to keep clean-slate semantics.
DROP TABLE IF EXISTS checkpoint_writes CASCADE;
DROP TABLE IF EXISTS checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS checkpoints CASCADE;
DROP TABLE IF EXISTS checkpoint_migrations CASCADE;

CREATE TABLE chat_threads (
  thread_id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT 'Untitled Thread',
  status TEXT NOT NULL DEFAULT 'active',
  docs_initialized BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_message_preview TEXT,
  next_seq BIGINT NOT NULL DEFAULT 1
);

CREATE TABLE chat_messages (
  id BIGSERIAL PRIMARY KEY,
  message_id TEXT NOT NULL,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  run_id TEXT,
  seq BIGINT NOT NULL,
  role TEXT NOT NULL,
  type TEXT,
  content JSONB NOT NULL,
  name TEXT,
  tool_call_id TEXT,
  tool_calls JSONB,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  by_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (thread_id, seq),
  UNIQUE (thread_id, message_id)
);

CREATE INDEX chat_messages_thread_seq_idx ON chat_messages(thread_id, seq);
CREATE INDEX chat_messages_thread_created_idx ON chat_messages(thread_id, created_at);
CREATE INDEX chat_messages_run_idx ON chat_messages(run_id);

CREATE TABLE docs (
  id BIGSERIAL PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  doc_id TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  description TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  updated_by TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (thread_id, doc_id)
);

CREATE INDEX docs_thread_idx ON docs(thread_id);

CREATE TABLE doc_versions (
  id BIGSERIAL PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  doc_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  content TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  updated_by TEXT,
  change_set_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (thread_id, doc_id, version)
);

CREATE INDEX doc_versions_thread_doc_idx ON doc_versions(thread_id, doc_id, version DESC);

CREATE TABLE runs (
  run_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  trigger TEXT NOT NULL DEFAULT 'chat',
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  error TEXT
);

CREATE INDEX runs_thread_started_idx ON runs(thread_id, started_at DESC);

CREATE TABLE agent_status_events (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  agent TEXT NOT NULL,
  status TEXT NOT NULL,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX agent_status_events_run_idx ON agent_status_events(run_id, created_at);

CREATE TABLE change_sets (
  change_set_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  run_id TEXT REFERENCES runs(run_id) ON DELETE SET NULL,
  created_by TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  decided_at TIMESTAMPTZ,
  decision_note TEXT
);

CREATE INDEX change_sets_thread_created_idx ON change_sets(thread_id, created_at DESC);

CREATE TABLE change_set_docs (
  id BIGSERIAL PRIMARY KEY,
  change_set_id TEXT NOT NULL REFERENCES change_sets(change_set_id) ON DELETE CASCADE,
  thread_id TEXT NOT NULL REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
  doc_id TEXT NOT NULL,
  before_content TEXT NOT NULL,
  after_content TEXT NOT NULL,
  diff TEXT NOT NULL,
  UNIQUE (change_set_id, doc_id)
);

CREATE INDEX change_set_docs_thread_idx ON change_set_docs(thread_id);

CREATE TABLE change_set_reviews (
  id BIGSERIAL PRIMARY KEY,
  change_set_id TEXT NOT NULL REFERENCES change_sets(change_set_id) ON DELETE CASCADE,
  decision TEXT NOT NULL,
  comment TEXT,
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX change_set_reviews_changeset_idx ON change_set_reviews(change_set_id, reviewed_at DESC);
