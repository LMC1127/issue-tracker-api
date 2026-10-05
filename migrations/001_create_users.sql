CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);