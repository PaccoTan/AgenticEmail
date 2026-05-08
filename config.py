import os

UPLOAD_FOLDER = "uploads"
EMAIL_FOLDER = "emails"
CONVERSATION_FOLDER = "conversations"
DATA_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EMAIL_FOLDER, exist_ok=True)
os.makedirs(CONVERSATION_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)