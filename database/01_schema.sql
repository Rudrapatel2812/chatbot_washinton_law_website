CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS jurisdictions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS laws (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id uuid NOT NULL REFERENCES jurisdictions(id),
    citation text NOT NULL,
    title_number text NOT NULL,
    chapter_number text NOT NULL,
    section_number text NOT NULL,
    heading text,
    text text NOT NULL,
    source_url text NOT NULL,
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'repealed', 'reserved', 'recodified', 'unknown')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, citation)
);

CREATE TABLE IF NOT EXISTS law_embeddings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    law_id uuid NOT NULL REFERENCES laws(id) ON DELETE CASCADE,
    provider text NOT NULL,
    model text NOT NULL,
    dimensions integer NOT NULL,
    embedding vector NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (law_id, provider, model)
);

CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content text NOT NULL,
    citations jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO jurisdictions (code, name)
VALUES
    ('WA', 'Washington State'),
    ('CA', 'California'),
    ('US-FED', 'United States Federal')
ON CONFLICT (code) DO NOTHING;
