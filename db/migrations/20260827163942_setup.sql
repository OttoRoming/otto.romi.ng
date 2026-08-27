-- migrate:up

CREATE TABLE passwords (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    password text NOT NULL,
    access_level smallint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE logins (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    password_id uuid REFERENCES passwords(id) ON DELETE SET NULL,
    user_agent TEXT,
    client_ip inet NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE sessions (
    token uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    access_level smallint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW()
);

-- migrate:down

DROP TABLE passwords;
DROP TABLE logins;
DROP TABLE sessions;

