-- Enable RLS on all public tables.
-- The backend connects with the service role key, which bypasses RLS.
-- No anon policies are defined, so direct public API access is blocked on every table.

ALTER TABLE jurisdictions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE laws            ENABLE ROW LEVEL SECURITY;
ALTER TABLE law_embeddings  ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations   ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages        ENABLE ROW LEVEL SECURITY;
