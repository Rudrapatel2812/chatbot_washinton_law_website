
from fastapi import FastAPI
import openai
import psycopg2
import re

app = FastAPI()
DB_CONFIG = {
    "dbname": "legal_db",
    "user": "legal_user",
    "password": "securepassword",
    "host": "localhost",
    "port": "5432"
}

# API key should be imported from environmnt variables
import os
from dotenv import load_dotenv

# load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
# Function to get a database connection
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Function to generate OpenAI embedding
def get_embedding(text):
    response = openai.embeddings.create(model="text-embedding-ada-002", input=[text])
    return response.data[0].embedding

def direct_rcw_lookup(title=None, chapter=None, section=None):
    """Directly look up RCW content based on title, chapter, and optional section"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, title, chapter, section, legal_text, citation_link FROM legal_records WHERE TRUE"
    params = []
    
    if title:
        query += " AND title ILIKE %s"
        params.append(f"%{title}%")
    
    if chapter:
        query += " AND chapter ILIKE %s"
        params.append(f"%{chapter}%")
    
    if section:
        query += " AND section ILIKE %s"
        params.append(f"%{section}%")
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return results

def extract_rcw_references(text):
    """Extract RCW references from the query text"""
    # Pattern for full RCW reference (Title, Chapter, Section)
    full_pattern = r"(?:RCW|rcw)?\s*(?:Title\s*)?(\d+)(?:\s*,?\s*Chapter\s*)?(\d+\.\d+)?(?:\s*,?\s*Section\s*)?(\d+\.\d+\.\d+)?"
    
    # Pattern for direct section reference without Title/Chapter prefix
    section_pattern = r"(?:RCW|rcw)?\s*(\d+\.\d+\.\d+)"
    
    # Try full pattern first
    match = re.search(full_pattern, text, re.IGNORECASE)
    if match:
        title, chapter, section = match.groups()
        return {
            "title": f"Title {title}" if title else None,
            "chapter": f"Chapter {chapter}" if chapter else None,
            "section": section
        }
    
    # Try direct section reference
    section_match = re.search(section_pattern, text, re.IGNORECASE)
    if section_match:
        section = section_match.group(1)
        # Extract title and chapter from section
        parts = section.split('.')
        if len(parts) >= 2:
            title = parts[0]
            chapter = f"{parts[0]}.{parts[1]}"
            return {
                "title": f"Title {title}",
                "chapter": f"Chapter {chapter}",
                "section": section
            }
    
    return None

def get_related_law(query_text):
    """Comprehensive search function that combines direct lookup with semantic search"""
    # Step 1: Check if the query contains RCW references
    rcw_refs = extract_rcw_references(query_text)
    
    # Step 2: If we have RCW references, try direct lookup first
    if rcw_refs:
        direct_results = direct_rcw_lookup(
            rcw_refs.get("title"), 
            rcw_refs.get("chapter"), 
            rcw_refs.get("section")
        )
        
        if direct_results:
            return {
                "result": direct_results[0],
                "method": "direct_lookup"
            }
    
    # Step 3: If direct lookup fails or no RCW reference, use semantic search
    query_embedding = get_embedding(query_text)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Using pgvector's L2 distance operator <-> for similarity search
    cursor.execute("""
        SELECT id, title, chapter, section, legal_text, citation_link
        FROM legal_records
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> %s
        LIMIT 1
    """, (query_embedding,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "result": result,
            "method": "semantic_search"
        }
    else:
        return None

def search_by_keywords(keywords):
    """Search for laws containing specific keywords"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, title, chapter, section, legal_text, citation_link FROM legal_records WHERE "
    conditions = []
    params = []
    
    for keyword in keywords:
        conditions.append("legal_text ILIKE %s")
        params.append(f"%{keyword}%")
    
    query += " AND ".join(conditions)
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    
    return results

@app.get("/query")
def query_law(question: str):
    try:
        # Check for specific keywords that might indicate a different type of query
        comparative_keywords = ["compare", "difference", "differ", "versus", "vs"]
        
        # Handle comparative questions
        if any(keyword in question.lower() for keyword in comparative_keywords):
            # For comparative questions, we might need to return multiple results
            keywords = re.findall(r'\b\w+\b', question.lower())
            keywords = [k for k in keywords if len(k) > 3]  # Filter out short words
            keyword_results = search_by_keywords(keywords[:3])  # Use top 3 keywords
            
            if keyword_results:
                response = {
                    "relevant_laws": []
                }
                for result in keyword_results[:2]:  # Return top 2 results for comparison
                    response["relevant_laws"].append({
                        "Title": result[1],
                        "Chapter": result[2],
                        "Section": result[3],
                        "Text": result[4],
                        "Citation": result[5]
                    })
                return response
        
        # Default case: direct or semantic search
        search_result = get_related_law(question)
        
        if not search_result:
            return {
                "message": "No matching laws found",
                "query": question
            }
        
        if "error" in search_result:
            return {"message": search_result["error"]}
        
        result = search_result.get("result")
        
        response = {
            "relevant_law": {
                "Title": result[1],
                "Chapter": result[2],
                "Section": result[3],
                "Text": result[4],
                "Citation": result[5]
            }
        }
        
        return response
    except Exception as e:
        return {"error": str(e), "query": question}

# Start the server with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
