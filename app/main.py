import os
import logging
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title=os.getenv("APP_NAME", "llm-transcript-rag"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import after environment variables are loaded
from . import storage, rag, utils


class QueryRequest(BaseModel):
    user_id: str
    transcript_id: str
    query: str


@app.post("/upload")
async def upload_transcript(
        background_tasks: BackgroundTasks,
        user_id: str = Form(...),
        transcript_name: str = Form(...),
        file: UploadFile = File(...)
):
    try:
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only text files are supported")

        content = await file.read()
        transcript_id = str(uuid.uuid4())

        # Process in background
        background_tasks.add_task(
            process_transcript,
            content.decode('utf-8'),
            user_id,
            transcript_id,
            transcript_name
        )

        return {
            "transcript_id": transcript_id,
            "message": "Processing started",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query")
async def query_transcript(request: QueryRequest):
    try:
        # Validate user access
        if not storage.has_transcript_access(request.user_id, request.transcript_id):
            raise HTTPException(status_code=403, detail="Access denied to transcript")

        # Check cache first
        cached_response = storage.get_cached_response(
            request.user_id,
            request.transcript_id,
            request.query
        )
        if cached_response:
            return cached_response

        # Process query
        result = rag.process_query(
            request.user_id,
            request.transcript_id,
            request.query
        )

        # Cache result
        storage.cache_response(
            request.user_id,
            request.transcript_id,
            request.query,
            result
        )

        # Save to query history
        storage.save_query_history(
            request.user_id,
            request.transcript_id,
            request.query,
            result
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/transcripts/{user_id}")
async def get_transcripts(user_id: str):
    try:
        return storage.get_user_transcripts(user_id)
    except Exception as e:
        logger.error(f"Failed to fetch transcripts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcripts: {str(e)}")


@app.get("/query-history/{user_id}")
async def get_query_history(user_id: str, transcript_id: Optional[str] = None, limit: int = 50):
    try:
        # Validate user access
        if transcript_id and not storage.has_transcript_access(user_id, transcript_id):
            raise HTTPException(status_code=403, detail="Access denied to transcript")

        history = storage.get_query_history(user_id, transcript_id, limit)
        return history
    except Exception as e:
        logger.error(f"Failed to fetch query history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch query history: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def process_transcript(content: str, user_id: str, transcript_id: str, name: str):
    try:
        # Use the new chunking function
        chunks, vectorstore = rag.process_and_store_transcript(content, user_id, transcript_id)

        # Save metadata
        storage.save_transcript_metadata(user_id, transcript_id, name, chunks)

        logger.info(f"Successfully processed transcript: {transcript_id} with {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Error processing transcript: {str(e)}")
        storage.save_processing_error(user_id, transcript_id, str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))