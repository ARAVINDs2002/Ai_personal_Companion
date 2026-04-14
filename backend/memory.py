import json
import logging
import os
import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Calculate paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
MEMORY_FILE = os.path.join(ROOT_DIR, "memory.json")
MAX_MEMORY = 100
DISTANCE_THRESHOLD = 1.6 # Adjusted for slightly more lenient matching

# Initialize model and FAISS index
logger.info("Initializing SentenceTransformer...")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)
except Exception as e:
    logger.error(f"Failed to load sentence-transformer: {e}")
    raise

# Persisted State
data = [] # List of {"text": "User: ...\nAI: ...", "timestamp": ...}
user_profile = {"name": None, "gender": None}
ai_profile = {"name": "Maya", "gender": "female"}

def load_memory():
    global data, user_profile, ai_profile, index
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                store = json.load(f)
                data = store.get("data", [])
                user_profile = store.get("user_profile", {"name": None, "gender": None})
                ai_profile = store.get("ai_profile", {"name": "Maya", "gender": "female"})
                if data:
                    texts = [item["text"] for item in data]
                    logger.info(f"Encoding {len(data)} old memory entries...")
                    embeddings = model.encode(texts)
                    index.add(np.array(embeddings).astype('float32'))
                    logger.info("Rebuilt FAISS index successfully.")
        except Exception as e:
            logger.error(f"Error loading memory from {MEMORY_FILE}: {e}")

def save_memory():
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump({
                "data": data, 
                "user_profile": user_profile, 
                "ai_profile": ai_profile
            }, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving memory to {MEMORY_FILE}: {e}")

def is_duplicate(new_text):
    recent = data[-10:]
    for item in recent:
        if item["text"] == new_text:
            return True
    return False

def add_memory(user_text, ai_text):
    global index, data
    new_text = f"User: {user_text}\nAI: {ai_text}"
    
    if is_duplicate(new_text):
        logger.warning("Duplicate memory detected, skipping addition.")
        return
        
    logger.info("Adding memory...")
    data.append({"text": new_text, "timestamp": time.time()})
    embedding = model.encode([new_text])
    
    if len(data) > MAX_MEMORY:
        logger.info("MAX_MEMORY hit. Evicting oldest memory and rebuilding FAISS flat index.")
        data.pop(0)
        index.reset()
        if data:
            texts = [item["text"] for item in data]
            embeddings = model.encode(texts)
            index.add(np.array(embeddings).astype('float32'))
    else:
        index.add(np.array(embedding).astype('float32'))
        
    save_memory()

def get_recent_memory(n=2):
    return data[-n:] if len(data) >= n else data

def search_memory(query, top_k=3):
    if not data:
        return "Memory:\n(No previous conversations)"
        
    logger.info("Searching memory...")
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding).astype('float32'), top_k)
    
    results = []
    count = 1
    
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1 and dist < DISTANCE_THRESHOLD:
            if idx < len(data):
                results.append(f"{count}. {data[idx]['text']}")
                count += 1
                
    if not results:
        logger.info("Memory retrieved, but all distance values exceeded threshold.")
        return "Memory:\n(No previous conversations)"
        
    memory_string = "Previous conversations:\n\n" + "\n\n".join(results)
    
    # Cap size dynamically
    if len(memory_string) > 500:
        memory_string = memory_string[:497] + "..."
        
    return memory_string

def clear_memory():
    global data, index
    data = []
    
    import faiss
    index = faiss.IndexFlatL2(dimension)
    
    save_memory()

# Attempt to load memory on module init
load_memory()
