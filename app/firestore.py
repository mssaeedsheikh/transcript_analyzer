import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Firebase only once
_firestore_client = None


def initialize_firebase():
    global _firestore_client
    try:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.getenv("FIRESTORE_PROJECT_ID")

        if not cred_path or not os.path.exists(cred_path):
            logger.warning(f"Firebase credentials not found at: {cred_path}")
            return None

        if not project_id:
            logger.warning("FIRESTORE_PROJECT_ID environment variable not set")
            return None

        # Check if already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'projectId': project_id
            })
            logger.info("Firebase initialized successfully")

        _firestore_client = firestore.client()
        return _firestore_client

    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        return None


def get_firestore_client():
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = initialize_firebase()
    return _firestore_client