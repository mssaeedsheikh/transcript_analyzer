# LLM Transcript Analyzer & RAG Summarizer (FastAPI)


# 5) Run server
uvicorn app.main:app --reload


# 6) Open docs
# http://127.0.0.1:8000/docs
```


## 🐳 Docker
```bash
# Build image
docker build -t llm-transcript-rag:latest .


# Run (mount a local ./data for Chroma persistence)
docker run --env-file .env -p 8000:8000 -v $(pwd)/data:/app/data llm-transcript-rag:latest
```


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


## 🧪 Sample cURL
```bash
# Upload transcript
curl -F "user_id=u123" -F "file=@samples/startup_fundraising.txt" http://127.0.0.1:8000/upload_transcript


# Ask a question
curl -X POST http://127.0.0.1:8000/query \
-H 'Content-Type: application/json' \
-d '{
"user_id":"u123",
"transcript_id":"startup_fundraising",
"question":"What are the biggest mistakes founders make while pitching investors?",
"top_k": 4
}'
```


## 📚 Deliverables
- ✅ Working FastAPI backend app
- ✅ Dockerfile
- ✅ README with setup
- ✅ Sample transcript
- 🎥 Provide your own 5‑min walkthrough using this README as script


---