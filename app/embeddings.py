from langchain_community.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
import os


def get_embeddings():
    provider = os.getenv("EMBEDDINGS_PROVIDER", "huggingface")

    if provider == "openai":
        return OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        # Force CPU usage to avoid CUDA issues
        return HuggingFaceEmbeddings(
            model_name=os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            model_kwargs={'device': 'cpu'}  # Force CPU usage
        )