#handles the "Neural Memory." It turns text into vectors and stores them.

import chromadb
from chromadb.utils import embedding_functions
import uuid

# Setup the Local Vector DB (Persists to disk)
CHROMA_DATA_PATH = "./voxguard_vectors"
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# 'all-MiniLM-L6-v2' is free and the industry standard for fast, local embeddings
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create (or get) the collection
collection = client.get_or_create_collection(
    name="video_segments",
    embedding_function=emb_fn
)

def vector_store_segments(video_id: str, title: str, segments: list):
    """
    Stores each verified transcript segment into the Vector DB.
    Allows for semantic searching later.
    """
    print(f"🧠 Vectorizing {len(segments)} memory segments...")
    
    ids = []
    documents = []
    metadatas = []

    for seg in segments:
        # We only store segments that are NOT suspicious to keep the "Brain" clean?
        # OR we store everything but tag the quality. Let's tag them.
        
        # Create a unique ID for this snippet
        chunk_id = f"{video_id}_{str(uuid.uuid4())[:8]}"
        
        ids.append(chunk_id)
        documents.append(seg['text'])
        metadatas.append({
            "video_id": video_id,
            "title": title,
            "start_time": seg['start'],
            "confidence": seg['confidence'],
            "is_flagged": True if seg['status'] == "⚠️ Suspicious" else False
        })

    # Add to ChromaDB in one batch
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ Indexed {len(segments)} segments into Vector Memory.")
    except Exception as e:
        print(f"❌ Vector Storage Error: {e}")

def query_memory(query_text: str, n_results=5):
    """
    Search the agent's brain for similar concepts.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results