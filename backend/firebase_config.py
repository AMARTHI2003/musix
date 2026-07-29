import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os

# Initialize Firebase Admin SDK
cred_path = os.path.join(os.path.dirname(__file__), "firebase-adminsdk.json")
cred = credentials.Certificate(cred_path)
firebase_app = firebase_admin.initialize_app(cred)

async def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")

def create_custom_token(uid: str) -> str:
    """Create a custom Firebase token for a user."""
    return firebase_auth.create_custom_token(uid).decode("utf-8")
