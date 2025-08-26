from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TranscriptChunk(BaseModel):
    text: str
    start_time: str
    end_time: str
    metadata: dict = {}

class QueryResponse(BaseModel):
    answer: str
    timestamps: List[dict]
    source_chunks: List[str]

class TranscriptMetadata(BaseModel):
    transcript_id: str
    name: str
    upload_date: datetime
    chunk_count: int