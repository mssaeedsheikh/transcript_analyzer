# LLM Transcript Analyzer and RAG Summarizer
A FastAPI backend service for analyzing and querying transcripts using Retrieval-Augmented Generation (RAG) with support for both Firestore and local storage.

## Features

- Transcript Upload and Indexing
  - Accept pre-formatted plain text files containing transcripts with timestamps
  - Token-aware chunking using LangChain text splitters
  - Extract start and end timestamps for each chunk 
  - Generate embeddings using OpenAI or HuggingFace 
  - Store embedded chunks in Chroma vector database

- Semantic Q&A with RAG 
  - Accept user queries on previously uploaded transcripts 
  - Perform similarity search using embedded chunks 
  - Use LangChain RAG flow to answer questions 
  - Response includes:
    - Concise, grounded answer 
    - List of timestamps where information appears 
    - Source transcript chunks for transparency

- Caching and Query History 
  - Cache previous queries per video per user to avoid redundant LLM calls 
  - Save query/response history in Firestore or local storage, scoped by user_id 
  - Configurable cache TTL (default: 7 days)

- User Access Control 
  - Users can only view and query their own transcripts and history 
  - User_id scoping and validation logic

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Firestore (Google Cloud) or Local JSON
- **Embeddings**: OpenAI or HuggingFace Sentence Transformers
- **LLM**: Ollama (local) or OpenAI API
- **Vector Store**: ChromaDB
- **Containerization**: Docker


## *Step 1 --- Set Up Firebase (Optional)*

**If using Firestore:**
- Create a Firebase project in the Firebase Console
- Enable Firestore Database
- Generate a service account key and download it as firebase-key.json
- Place the key file in the project root directory
- Update the FIRESTORE_PROJECT_ID in your .env file

## *Step 2 --- Set Up LLM*
- setup *ollama* on local or on remote if not using OpenAI because of limitations of paid account
- for installing ollama use Docker installation process

## *Step 3 --- Build and Run with Docker*
```bash
# Build the Docker image
docker build -t transcript-analyzer .

# Run the container
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data transcript-analyzer
```

## *Step 4 --- Access the Application*
- The API will be available at http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## User ID Flow

The application uses a simple user ID-based authentication system where:

1. Each user is identified by a unique user_id string 
2. All data (transcripts, queries, query_history) is scoped to the user_id 
3. Users can only access their own data 
4. The user_id is passed in all API requests

### How to Use User IDs
1. Choose a user identification system: You can use:
   - Email addresses 
   - Database IDs 
   - UUIDs 
   - Authentication tokens (JWT sub claims)
2. Pass the user_id in all requests:
   - Upload: user_id form field 
   - Query: user_id in JSON body 
   - History: user_id in URL path
3. Example workflow:
```bash
    # 1. Upload a transcript for a user
    curl -X POST -F "user_id=user123@example.com" \
      -F "transcript_name=My Podcast" \
      -F "file=@podcast.txt" \
      http://localhost:8000/upload
    
    # 2. Query the transcript
    curl -X POST -H "Content-Type: application/json" \
      -d '{"user_id": "user123@example.com", "transcript_id": "abc123", "query": "What was discussed?"}' \
      http://localhost:8000/query
    
    # 3. Get query history
    curl "http://localhost:8000/query-history/user123@example.com?transcript_id=abc123&limit=10"
```
## Query History Flow
The application automatically saves all queries and responses to a query history, which can be retrieved later.

### How to Use Query History
1. Automatic Saving: All queries are automatically saved to history
2. **Retrieve History:**
```bash
    # Get all query history for a user
    curl "http://localhost:8000/query-history/user123@example.com?limit=20"
    
    # Get query history for a specific transcript
    curl "http://localhost:8000/query-history/user123@example.com?transcript_id=abc123&limit=10"
```
3. **History Response Format:**
```json
[
  {
    "query_id": "unique-query-id",
    "user_id": "user123@example.com",
    "transcript_id": "abc123",
    "query": "What was discussed?",
    "response": {
      "answer": "The podcast discussed...",
      "timestamps": [{"start": "00:01:30", "end": "00:02:10"}],
      "source_chunks": ["One of the topics discussed was..."]
    },
    "timestamp": "2025-08-27T02:58:15.340000",
    "type": "query_history"
  }
]
```
4. **Use Cases:**
   - Display previous queries to users
   - Avoid redundant processing 
   - Analyze user behavior 
   - Implement "saved queries" functionality


## Firestore Indexes
If using Firestore, you need to create indexes for optimal performance. Firestore requires indexes for queries that:
1. Filter on multiple fields 
2. Order by a field with filtering on different fields

### Required Indexes
1. **For query history:**
   - Collection: query_history 
   - Fields: user_id (Ascending), timestamp (Descending)
   - Fields: user_id (Ascending), transcript_id (Ascending), timestamp (Descending)
2. **For transcripts:**
   - Collection: transcripts
   - Fields: user_id (Ascending)
3. **For queries cache:**
   - Collection: queries
   - Fields: user_id (Ascending), transcript_id (Ascending), query (Ascending), timestamp (Descending)

### How to Create Indexes
1. Go to the Firebase Console 
2. Select your project 
3. Go to Firestore Database → Indexes 
4. Click "Create Index"
5. Enter the collection and field configurations as above

Alternatively, you can let Firestore create the indexes automatically by running the queries first and following the link in the error message.


## *Step 5 ---  API Usage*

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
Example Response:
```json
{
  "answer": "Founders often focus too much on their product and not enough on the market...",
  "timestamps": [
    {"start": "00:01:30", "end": "00:02:10"},
    {"start": "00:03:45", "end": "00:04:10"}
  ],
  "source_chunks": [
    "One of the biggest mistakes founders make is focusing too much on the product...",
    "Another issue is when founders don't handle criticism well during Q&A..."
  ]
}
```

### Get User Transcripts
```bash
curl http://localhost:8000/transcripts/{user123}
```

## *Step 6 --- Development*

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
### Environment Configuration
Create a .env file in the root directory:
```env
# Core
APP_NAME=llm-transcript-rag
ENV=dev
PORT=8000

# Storage paths
DATA_DIR=./data
CHROMA_DIR=./data/chroma
LOCAL_JSON_DB=./data/local_store.json

# Embeddings
EMBEDDINGS_PROVIDER=huggingface
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM
LLM_PROVIDER=ollama
OPENAI_MODEL=gpt-4o-mini
OLLAMA_MODEL=mistral

# Firestore (optional)
GOOGLE_APPLICATION_CREDENTIALS=./firebase-key.json
FIRESTORE_PROJECT_ID=your_firestore_project_id

# Caching
CACHE_TTL_SECONDS=604800

# Chunking configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```
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
- `POST /upload_transcript` — form-data: `user_id`, file: `file` (.txt), `transcript_name`
- `POST /query` — JSON: `{ user_id, transcript_id, query, top_k? }`
- `GET /transcripts` — query: `user_id`
- `GET /history` — query: `user_id`, `transcript_id`, `limit`


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