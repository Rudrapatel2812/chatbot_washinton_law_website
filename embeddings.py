import openai
import psycopg2
import numpy as np
import os

# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

DB_CONFIG = {
    "dbname": "legal_db",
    "user": "legal_user",
    "password": "securepassword",
    "host": "localhost",
    "port": "5432"
}

def generate_embedding(text):
    """Generate OpenAI embedding for a given text."""
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return np.array(response["data"][0]["embedding"], dtype=np.float32)

def update_embeddings():
    """Generate embeddings for legal records that do not have embeddings."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT id, legal_text FROM legal_records WHERE embedding IS NULL;")
        rows = cursor.fetchall()

        if not rows:
            print("✅ All records already have embeddings.")
            return

        print(f"🔄 Generating embeddings for {len(rows)} records...")

        for row in rows:
            embedding = generate_embedding(row[1])  # NumPy array
            embedding_bytes = embedding.tobytes()  # Convert to bytes

            cursor.execute("UPDATE legal_records SET embedding = %s WHERE id = %s", (embedding_bytes, row[0]))

        conn.commit()
        print("✅ Embeddings updated successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()

update_embeddings()

