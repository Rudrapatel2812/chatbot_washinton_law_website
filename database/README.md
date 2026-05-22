# Database

Run migrations in order from the Supabase SQL editor.

`law_embeddings.embedding` uses pgvector's flexible `vector` type so multiple embedding models can be stored. Retrieval always filters by model before comparing vectors. Add one partial vector index per production embedding model and dimension.
