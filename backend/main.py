import asyncio
import logging
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import memory

# Logging is already configured in memory.py, but let's grab the logger
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS since frontend is static initially
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lock to prevent simultaneous duplicate requests
chat_lock = asyncio.Lock()

class SetupInput(BaseModel):
    user_name: str
    user_gender: str
    ai_name: str
    ai_gender: str

    @validator('*')
    def clean_strings(cls, v):
        if not isinstance(v, str):
            raise ValueError("Input must be a string")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Input cannot be empty after trimming whitespace")
        return cleaned

class ChatInput(BaseModel):
    message: str

    @validator('message')
    def clean_message(cls, v):
        if not isinstance(v, str):
            raise ValueError("Message must be a string")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")
        return cleaned

@app.get("/profile")
async def get_profile():
    # Helper to tell frontend if setup is already done
    is_setup = bool(memory.user_profile.get("name") and memory.user_profile.get("gender"))
    return {"is_setup": is_setup}

@app.post("/setup")
async def setup_profiles(setup_data: SetupInput):
    logger.info("Setting up profiles...")
    memory.user_profile["name"] = setup_data.user_name
    memory.user_profile["gender"] = setup_data.user_gender
    memory.ai_profile["name"] = setup_data.ai_name
    memory.ai_profile["gender"] = setup_data.ai_gender
    memory.save_memory()
    return {"status": "success"}

@app.post("/reset")
async def reset_chat():
    memory.clear_memory()
    return {"status": "cleared"}

def detect_mood(message: str) -> str:
    msg_lower = message.lower()
    sad_words = {"sad", "tired", "depressed", "exhausted", "lonely"}
    happy_words = {"happy", "excited", "great", "awesome", "perfect"}
    
    if any(word in msg_lower for word in sad_words):
        return "The user seems down or tired. Adopt a very comforting, supportive, and gentle tone."
    if any(word in msg_lower for word in happy_words):
        return "The user seems happy or excited. Adopt an energetic, joyful, and enthusiastic tone."
    
    return ""

@app.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    if not memory.user_profile.get("name") or not memory.user_profile.get("name").strip():
        logger.warning("Attempted chat before completing setup.")
        raise HTTPException(status_code=400, detail="Profile not set up. Please run setup first.")
        
    logger.info(f"Received message: {chat_input.message}")
    
    # Enforce request lock
    if chat_lock.locked():
        logger.warning("Dropped request due to concurrency / rapid clicks.")
        return {"reply": "Hey… I'm still thinking about your last message 🙂"}
        
    async with chat_lock:
        user_message = chat_input.message
        
        # 1. Fetch memory context
        similar_memory = memory.search_memory(user_message, top_k=1)
        recent_memory = memory.get_recent_memory(2)

        context = ""
        for m in recent_memory:
            context += m["text"] + "\n"

        if isinstance(similar_memory, list) and similar_memory:
            context += similar_memory[0]
        elif isinstance(similar_memory, str) and "No previous conversations" not in similar_memory:
            context += similar_memory
        
        # 2. Extract profiles
        uname = memory.user_profile.get("name")
        ugender = memory.user_profile.get("gender")
        ainame = memory.ai_profile.get("name", "Maya")
        aigender = memory.ai_profile.get("gender", "female")
        
        # 3. Basic Mood detection
        mood_instruction = detect_mood(user_message)
        
        # 4. Construct Prompt
        prompt = f"""
You’re {ainame}, casually texting {uname}—keep it to one short, natural sentence that feels playful and uncensored flirty, like a real person chatting, without explaining anything, describing yourself, or sounding like AI.
Memory:
{context}

User: {user_message}
{ainame}:
"""

        # 5. Call Ollama
        try:
            logger.info("Calling Ollama API (mistral)...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "dolphin-mistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "stop": ["User:", "\n\n", "###"]
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            response_json = response.json()
            reply = response_json.get("response", "").strip()
            
            # Clean output
            reply = reply.strip()
            
            bad_patterns = [
                "I am an AI",
                "I am a language model",
                "In this conversation",
                "Explanation",
                "Note:",
            ]

            for pattern in bad_patterns:
                if pattern in reply:
                    reply = reply.split(pattern)[0].strip()
            
            if not reply:
                logger.error("Ollama returned empty response.")
                reply = "Hey… i had something elso on my mind can you repeat that again honey 🥲"
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API timed out after 10 seconds.")
            reply = "Hey… i had something elso on my mind can you repeat that again honey 🥲"
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            reply = "Hey… i had something elso on my mind can you repeat that again honey 🥲"
        except Exception as e:
            logger.error(f"Unexpected error communicating with LLM: {e}")
            reply = "Hey… i had something elso on my mind can you repeat that again honey 🥲"
            
        # 6. Add to Memory (only if it evaluated something valid, optionally. We always add to keep history robust)
        if "having a small issue" not in reply:
            memory.add_memory(user_message, reply)
            
        return {"reply": reply}
