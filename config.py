import os
from dotenv import load_dotenv
load_dotenv()

USER = os.getenv("USER_NAME")
UPLOAD_FOLDER = "uploads"
EMAIL_FOLDER = "emails"
CONVERSATION_FOLDER = "conversations"
DATA_FOLDER = "data"
GENERATED_DOCUMENTS_FOLDER = "documents"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EMAIL_FOLDER, exist_ok=True)
os.makedirs(CONVERSATION_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(GENERATED_DOCUMENTS_FOLDER, exist_ok=True)