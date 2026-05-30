CREATE INDEX IF NOT EXISTS idx_laws_jurisdiction_citation
    ON laws (jurisdiction_id, citation);

CREATE INDEX IF NOT EXISTS idx_laws_title_chapter
    ON laws (jurisdiction_id, title_number, chapter_number);

CREATE INDEX IF NOT EXISTS idx_law_embeddings_model
    ON law_embeddings (model);

CREATE INDEX IF NOT EXISTS idx_law_embeddings_openai_small_hnsw
    ON law_embeddings
    USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
    WHERE model = 'text-embedding-3-small';

CREATE INDEX IF NOT EXISTS idx_conversations_user_created
    ON conversations (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
    ON messages (conversation_id, created_at ASC);
