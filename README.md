# LLM Transcript Analyzer and RAG Summarizer
A FastAPI backend service for analyzing and querying transcripts using Retrieval-Augmented Generation (RAG) with support for both Firestore and local storage.

## Features

- Transcript upload and indexing with timestamp extraction
- Semantic Q&A with RAG using OpenAI or HuggingFace embeddings
- Query caching and history
- User access control and data isolation
- Support for both Firestore and local JSON storage
- Docker containerization

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Firestore (Google Cloud) or Local JSON
- **Embeddings**: OpenAI or HuggingFace Sentence Transformers
- **LLM**: Ollama (local) or OpenAI API
- **Vector Store**: ChromaDB
- **Containerization**: Docker


1. **Step 1 --- Set Up Firebase (Optional)**

**If using Firestore:**
- Create a Firebase project in the Firebase Console
- Enable Firestore Database
- Generate a service account key and download it as firebase-key.json
- Place the key file in the project root directory
- Update the FIRESTORE_PROJECT_ID in your .env file

2. **Step 2 --- Build and Run with Docker**
```bash
# Build the Docker image
docker build -t transcript-analyzer .

# Run the container
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data transcript-analyzer
```

3. **Step 3 --- Access the Application**
- The API will be available at http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

4. **Step 4 ---  API Usage**

### Upload a Transcript
```bash
curl -X POST -F "user_id=user123" \
  -F "transcript_name=Startup Fundraising Tips" \
  -F "file=@path/to/transcript.txt" \
  http://localhost:8000/upload
```
Example transcript format:
```text
[00:00:00] Welcome to this talk on startup fundraising...
[00:01:30] One of the biggest mistakes founders make is focusing too much on the product...
[00:02:10] Founders often overlook market research...
```

### Query a Transcript
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "transcript_id": "transcript_id", "query": "What are the main points?"}' \
  http://localhost:8000/query
```

### Get User Transcripts
```bash
curl http://localhost:8000/transcripts/{user123}
```

5. **Step 5 --- Development**

### Without Docker
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure
```text
transcript_analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # Pydantic models
│   ├── storage.py       # Firestore and local storage implementations
│   ├── embeddings.py    # Embedding providers (OpenAI/HuggingFace)
│   ├── rag.py          # RAG processing and query handling
│   ├── utils.py        # Utility functions (transcript parsing)
│   ├── firestore.py    # Firebase initialization
│   └── config.py       # Configuration management
├── data/               # Data directory (mounted in Docker)
│   ├── chroma/         # ChromaDB vector store
│   └── local_store.json # Local JSON database (if not using Firestore)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env               # Environment variables (create from .env.example)
├── .gitignore
└── README.md
```

## Configuration Options

### Storage Backend
The application can use either Firestore or local JSON storage:
- Firestore: Set *FIRESTORE_PROJECT_ID* and provide *firebase-key.json*
- Local JSON: Don't set Firestore environment variables (data stored in *data/local_store.json*)

### Embedding Providers
- HuggingFace (default): Set *EMBEDDINGS_PROVIDER=huggingface*
- OpenAI: Set *EMBEDDINGS_PROVIDER=openai* and provide *OPENAI_API_KEY*

### LLM Providers
- Ollama (default): Set *LLM_PROVIDER=ollama*
- OpenAI: Set *LLM_PROVIDER=openai* and provide *OPENAI_API_KEY*

### Common Issues
- Firestore not connecting: Check your firebase-key.json and project ID
- CUDA errors: The application will automatically fall back to CPU mode
- Port already in use: Change the PORT in your .env file


## 📦 API Overview
- `POST /upload_transcript` — form-data: `user_id`, file: `file` (.txt)
- `POST /query` — JSON: `{ user_id, transcript_id, question, top_k? }`
- `GET /transcripts` — query: `user_id`
- `GET /history` — query: `user_id`, `transcript_id`


### Input Transcript Format (example)
```
[00:00:00] Welcome to this talk on startup fundraising...
[00:01:30] One of the biggest mistakes founders make is focusing too much on the product...
[00:02:10] Founders often overlook market research...
```


## 🔧 Switching Models
- Embeddings: set `EMBEDDINGS_PROVIDER=openai|huggingface`
- LLM: `LLM_PROVIDER=openai|ollama`
- `OLLAMA_MODEL=mistral` (example) and run `ollama serve`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini` (example)