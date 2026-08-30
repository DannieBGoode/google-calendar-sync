PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS installation_admin (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    token_hash TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state_hash TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
);

CREATE TABLE IF NOT EXISTS connected_accounts (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL CHECK (provider = 'google'),
    display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    encrypted_credentials BLOB NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (provider, email)
);

CREATE TABLE IF NOT EXISTS sync_rules (
    id TEXT PRIMARY KEY,
    source_account_id TEXT NOT NULL,
    source_calendar_id TEXT NOT NULL,
    destination_account_id TEXT NOT NULL,
    destination_calendar_id TEXT NOT NULL,
    privacy_policy TEXT NOT NULL,
    all_day_policy TEXT NOT NULL,
    busy_title TEXT NOT NULL,
    initial_lookback_days INTEGER NOT NULL CHECK (initial_lookback_days >= 0),
    state TEXT NOT NULL,
    UNIQUE (
        source_account_id,
        source_calendar_id,
        destination_account_id,
        destination_calendar_id
    )
);

CREATE TABLE IF NOT EXISTS event_mappings (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL REFERENCES sync_rules(id) ON DELETE CASCADE,
    source_account_id TEXT NOT NULL,
    source_calendar_id TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    destination_account_id TEXT NOT NULL,
    destination_calendar_id TEXT NOT NULL,
    destination_event_id TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    projection_fingerprint TEXT NOT NULL,
    UNIQUE (rule_id, source_account_id, source_calendar_id, source_event_id),
    UNIQUE (rule_id, destination_account_id, destination_calendar_id, destination_event_id)
);

CREATE TABLE IF NOT EXISTS sync_cursors (
    rule_id TEXT PRIMARY KEY REFERENCES sync_rules(id) ON DELETE CASCADE,
    cursor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS destination_sync_cursors (
    rule_id TEXT PRIMARY KEY REFERENCES sync_rules(id) ON DELETE CASCADE,
    cursor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    source_event_id TEXT,
    destination_event_id TEXT,
    detail TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    deduplication_key TEXT NOT NULL UNIQUE,
    rule_id TEXT,
    category TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('open', 'resolved')),
    summary TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS rule_failures (
    rule_id TEXT PRIMARY KEY REFERENCES sync_rules(id) ON DELETE CASCADE,
    consecutive_failures INTEGER NOT NULL,
    last_category TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
