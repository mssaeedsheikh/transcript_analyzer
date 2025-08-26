import json
import os
import logging
import uuid  # Add this import
from datetime import datetime, timedelta
from .firestore import get_firestore_client
from google.cloud import firestore

logger = logging.getLogger(__name__)


def get_db():
    firestore_client = get_firestore_client()
    if firestore_client:
        logger.info("Using Firestore for database operations")
        return FirestoreDB(firestore_client)
    logger.info("Using local JSON for database operations")
    return LocalJSONDB()


class LocalJSONDB:
    def __init__(self):
        self.path = os.getenv("LOCAL_JSON_DB", "./data/local_store.json")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        logger.info(f"Local JSON DB path: {self.path}")

    def _read_data(self):
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"transcripts": {}, "queries": {}, "errors": {}, "query_history": {}}

    def _write_data(self, data):
        with open(self.path, 'w') as f:
            json.dump(data, f, default=str)

    def save_transcript_metadata(self, user_id, transcript_id, name, chunks):
        try:
            data = self._read_data()
            metadata = {
                "user_id": user_id,
                "transcript_id": transcript_id,
                "name": name,
                "upload_date": datetime.now().isoformat(),
                "chunk_count": len(chunks),
                "status": "processed"
            }

            if "transcripts" not in data:
                data["transcripts"] = {}

            data["transcripts"][transcript_id] = metadata
            self._write_data(data)
            logger.info(f"Saved transcript metadata to local JSON: {transcript_id}")
        except Exception as e:
            logger.error(f"Error saving transcript metadata to local JSON: {e}")

    def has_transcript_access(self, user_id, transcript_id):
        try:
            data = self._read_data()
            transcript = data.get("transcripts", {}).get(transcript_id, {})
            return transcript.get("user_id") == user_id
        except Exception as e:
            logger.error(f"Error checking transcript access in local JSON: {e}")
            return False

    def get_cached_response(self, user_id, transcript_id, query):
        try:
            # Find all queries for this user and transcript
            data = self._read_data()
            ttl = int(os.getenv("CACHE_TTL_SECONDS", 604800))

            for query_id, query_data in data.get("queries", {}).items():
                if (query_data.get("user_id") == user_id and
                        query_data.get("transcript_id") == transcript_id and
                        query_data.get("query") == query):

                    cache_time = datetime.fromisoformat(query_data["timestamp"])
                    if (datetime.now() - cache_time).total_seconds() < ttl:
                        return query_data["response"]

            return None
        except Exception as e:
            logger.error(f"Error getting cached response from local JSON: {e}")
            return None

    def cache_response(self, user_id, transcript_id, query, response):
        try:
            # Generate a unique query ID
            query_id = str(uuid.uuid4())

            cache_data = {
                "query_id": query_id,
                "user_id": user_id,
                "transcript_id": transcript_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

            data = self._read_data()
            if "queries" not in data:
                data["queries"] = {}

            data["queries"][query_id] = cache_data
            self._write_data(data)
            logger.info(f"Cached response in local JSON: {query_id}")
        except Exception as e:
            logger.error(f"Error caching response in local JSON: {e}")

    def save_processing_error(self, user_id, transcript_id, error_message):
        try:
            error_data = {
                "user_id": user_id,
                "transcript_id": transcript_id,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }

            data = self._read_data()
            if "errors" not in data:
                data["errors"] = {}

            data["errors"][transcript_id] = error_data
            self._write_data(data)
            logger.info(f"Saved processing error to local JSON: {transcript_id}")
        except Exception as e:
            logger.error(f"Error saving processing error to local JSON: {e}")

    def get_user_transcripts(self, user_id):
        try:
            data = self._read_data()
            # Filter transcripts by user_id
            user_transcripts = {}
            for transcript_id, transcript_data in data.get("transcripts", {}).items():
                if transcript_data.get("user_id") == user_id:
                    user_transcripts[transcript_id] = transcript_data

            return user_transcripts
        except Exception as e:
            logger.error(f"Error getting user transcripts from local JSON: {e}")
            return {}

    def get_query_history(self, user_id: str, transcript_id: str = None, limit: int = 50):
        """Get query history for user, optionally filtered by transcript"""
        try:
            data = self._read_data()
            history = []

            # If no query_history exists, return empty list
            if "query_history" not in data:
                return history

            # Filter by user_id and optionally transcript_id
            for query_id, query_data in data["query_history"].items():
                if query_data["user_id"] == user_id:
                    if transcript_id is None or query_data["transcript_id"] == transcript_id:
                        history.append(query_data)

            # Sort by timestamp descending and limit
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            return history[:limit]
        except Exception as e:
            logger.error(f"Error getting query history from local JSON: {e}")
            return []

    def save_query_history(self, user_id: str, transcript_id: str, query: str, response: dict):
        """Save complete query history"""
        try:
            query_id = str(uuid.uuid4())
            query_data = {
                "query_id": query_id,
                "user_id": user_id,
                "transcript_id": transcript_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "type": "query_history"
            }

            data = self._read_data()
            if "query_history" not in data:
                data["query_history"] = {}

            data["query_history"][query_id] = query_data
            self._write_data(data)
            logger.info(f"Saved query history to local JSON: {query_id}")
        except Exception as e:
            logger.error(f"Error saving query history to local JSON: {e}")


class FirestoreDB:
    def __init__(self, client):
        self.client = client
        logger.info("FirestoreDB initialized")

    def save_transcript_metadata(self, user_id, transcript_id, name, chunks):
        try:
            metadata = {
                "user_id": user_id,
                "transcript_id": transcript_id,
                "name": name,
                "upload_date": datetime.now().isoformat(),
                "chunk_count": len(chunks),
                "status": "processed"
            }

            # Save as a document in the transcripts collection
            doc_ref = self.client.collection("transcripts").document(transcript_id)
            doc_ref.set(metadata)
            logger.info(f"Saved transcript metadata to Firestore: {transcript_id} for user: {user_id}")
        except Exception as e:
            logger.error(f"Error saving transcript metadata to Firestore: {e}")

    def has_transcript_access(self, user_id, transcript_id):
        try:
            # Get the transcript document
            doc_ref = self.client.collection("transcripts").document(transcript_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                # Check if the user_id matches
                return data.get("user_id") == user_id
            return False
        except Exception as e:
            logger.error(f"Error checking transcript access in Firestore: {e}")
            return False

    def get_cached_response(self, user_id, transcript_id, query):
        try:
            ttl = int(os.getenv("CACHE_TTL_SECONDS", 604800))

            # Query for matching documents using filter keyword argument
            queries_ref = self.client.collection("queries")
            query_ref = queries_ref.where(
                filter=firestore.FieldFilter("user_id", "==", user_id)
            ).where(
                filter=firestore.FieldFilter("transcript_id", "==", transcript_id)
            ).where(
                filter=firestore.FieldFilter("query", "==", query)
            ).order_by(
                "timestamp", direction="DESCENDING"
            ).limit(1)

            docs = query_ref.stream()

            for doc in docs:
                cached_data = doc.to_dict()
                cache_time = datetime.fromisoformat(cached_data["timestamp"])
                if (datetime.now() - cache_time).total_seconds() < ttl:
                    return cached_data["response"]

            return None
        except Exception as e:
            logger.error(f"Error getting cached response from Firestore: {e}")
            return None

    def cache_response(self, user_id, transcript_id, query, response):
        try:
            # Generate a unique query ID
            query_id = str(uuid.uuid4())

            cache_data = {
                "query_id": query_id,
                "user_id": user_id,
                "transcript_id": transcript_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

            # Save as a document in the queries collection
            doc_ref = self.client.collection("queries").document(query_id)
            doc_ref.set(cache_data)
            logger.info(f"Cached response in Firestore: {query_id}")
        except Exception as e:
            logger.error(f"Error caching response in Firestore: {e}")

    def save_processing_error(self, user_id, transcript_id, error_message):
        try:
            error_data = {
                "user_id": user_id,
                "transcript_id": transcript_id,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }

            # Save as a document in the errors collection
            doc_ref = self.client.collection("errors").document(transcript_id)
            doc_ref.set(error_data)
            logger.info(f"Saved processing error to Firestore: {transcript_id}")
        except Exception as e:
            logger.error(f"Error saving processing error to Firestore: {e}")

    def get_user_transcripts(self, user_id):
        try:
            # Query all transcripts where user_id matches using filter keyword argument
            transcripts_ref = self.client.collection("transcripts")
            query = transcripts_ref.where(
                filter=firestore.FieldFilter("user_id", "==", user_id)
            )
            docs = query.stream()

            transcripts = {}
            for doc in docs:
                transcripts[doc.id] = doc.to_dict()

            return transcripts
        except Exception as e:
            logger.error(f"Error getting user transcripts from Firestore: {e}")
            return {}

    def save_query_history(self, user_id: str, transcript_id: str, query: str, response: dict):
        """Save complete query history"""
        try:
            query_id = str(uuid.uuid4())
            query_data = {
                "query_id": query_id,
                "user_id": user_id,
                "transcript_id": transcript_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "type": "query_history"
            }

            doc_ref = self.client.collection("query_history").document(query_id)
            doc_ref.set(query_data)
            logger.info(f"Saved query history: {query_id}")
        except Exception as e:
            logger.error(f"Error saving query history: {e}")

    def get_query_history(self, user_id: str, transcript_id: str = None, limit: int = 50):
        """Get query history for user, optionally filtered by transcript"""
        try:
            query_ref = self.client.collection("query_history")
            query = query_ref.where(
                filter=firestore.FieldFilter("user_id", "==", user_id)
            )

            if transcript_id:
                query = query.where(
                    filter=firestore.FieldFilter("transcript_id", "==", transcript_id)
                )

            query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)

            docs = query.stream()
            history = []

            for doc in docs:
                history.append(doc.to_dict())

            return history
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []

    # Add similar methods to LocalJSONDB class



# Helper functions
def save_transcript_metadata(user_id, transcript_id, name, chunks):
    db = get_db()
    db.save_transcript_metadata(user_id, transcript_id, name, chunks)

def has_transcript_access(user_id, transcript_id):
    db = get_db()
    return db.has_transcript_access(user_id, transcript_id)

def get_cached_response(user_id, transcript_id, query):
    db = get_db()
    return db.get_cached_response(user_id, transcript_id, query)

def cache_response(user_id, transcript_id, query, response):
    db = get_db()
    db.cache_response(user_id, transcript_id, query, response)

# FIXED: These functions were calling the wrong methods
def save_query_history(user_id, transcript_id, query, response):
    db = get_db()
    db.save_query_history(user_id, transcript_id, query, response)  # Fixed: was calling cache_response

def get_query_history(user_id, transcript_id=None, limit=50):
    db = get_db()
    return db.get_query_history(user_id, transcript_id, limit)  # Fixed: was calling get_cached_response

def save_processing_error(user_id, transcript_id, error_message):
    db = get_db()
    db.save_processing_error(user_id, transcript_id, error_message)

def get_user_transcripts(user_id):
    db = get_db()
    return db.get_user_transcripts(user_id)