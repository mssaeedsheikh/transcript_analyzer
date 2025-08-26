import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # Core
    APP_NAME = os.getenv("APP_NAME", "llm-transcript-rag")
    ENV = os.getenv("ENV", "dev")
    PORT = int(os.getenv("PORT", 8000))

    # Storage paths
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
    LOCAL_JSON_DB = os.getenv("LOCAL_JSON_DB", "./data/local_store.json")

    # Embeddings
    EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "huggingface")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

    # Firestore
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")

    # Caching
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 604800))  # 7 days