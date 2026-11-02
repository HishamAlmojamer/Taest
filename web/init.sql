-- init.sql
-- Additional tables for the web system (non-destructive)
-- The existing tables are created by the Python backend's create_tables()

-- NOTE: this script runs on a brand-new PostgreSQL container BEFORE the
-- FastAPI backend creates the `users` table. Therefore the user_id columns
-- must NOT declare an inline FK to users here (it would abort init with
-- "relation users does not exist"). Foreign keys are added later by the
-- backend's additive migration logic once `users` exists.

-- Refresh tokens for JWT
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    title TEXT NOT NULL,
    message TEXT,
    type TEXT DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    link TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
