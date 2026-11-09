CREATE TABLE IF NOT EXISTS ip_country_map (
    ip_address INET PRIMARY KEY,
    country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS authentication_attempts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_key TEXT NOT NULL UNIQUE,
    event_month TEXT NOT NULL,
    event_day SMALLINT NOT NULL,
    event_time TIME NOT NULL,
    username TEXT NOT NULL,
    ip_address INET NOT NULL,
    country TEXT NOT NULL DEFAULT 'Unknown',
    status TEXT NOT NULL CHECK (status IN ('Accepted', 'Failed')),
    method TEXT NOT NULL,
    invalid_user BOOLEAN NOT NULL DEFAULT FALSE,
    attempt_count INTEGER NOT NULL DEFAULT 1 CHECK (attempt_count > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attempts_country_status
    ON authentication_attempts (country, status);
CREATE INDEX IF NOT EXISTS idx_attempts_user_status
    ON authentication_attempts (username, status);
CREATE INDEX IF NOT EXISTS idx_attempts_invalid_user
    ON authentication_attempts (invalid_user, status);
