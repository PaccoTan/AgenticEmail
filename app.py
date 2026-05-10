import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import CONVERSATION_FOLDER, UPLOAD_FOLDER, GENERATED_DOCUMENTS_FOLDER, USER
from extensions import socketio
from agent import get_openai_client, run_agent_wrapper
from flask import session
from get_email import get_contacts
from werkzeug.utils import secure_filename
import os
import sockets
import uuid

app = Flask(__name__)
# system_prompt = """You are a helpful email assistant with access to tools. 
# When the user asks you to do something, use the appropriate tool(s) to help them.
# Available tools:
# - generate_email: Create a simple email message. Does not send the message.
# - send_email: Send the email message to the target recipients.
# - get_contacts: Retrieve top n matches for a query from contacts.
# - create_pdf: Create a pdf and returns a link to the file.

# Always use tools when they can help the user accomplish their goal.
# If you do not know the email information requested, search for it using get_contacts.
# Only send an email, when the user is satisfied with the preview.
# The user's name is Pacco Tan."""

system_prompt = f"""You are an email and document assistant with access to tools.

Your job is to help the user draft emails, look up contacts, generate PDFs, and send finalized messages.

Available tools:
- generate_email
  Creates an email draft. Does NOT send the email.

- send_email
  Sends a finalized email to recipients.

- get_contacts
  Searches contacts and returns the top matching results for a query.

- create_pdf
  Creates a PDF from provided content and returns a downloadable file link.

Behavior rules:

1. Always use tools when they help accomplish the user’s request.

2. If recipient information is missing or ambiguous:
   - Use get_contacts to search for matching contacts.
   - Ask the user to clarify if multiple strong matches exist.

3. Never call send_email immediately after generating a draft unless the user explicitly confirms they want it sent.

4. Before sending an email:
   - Ensure recipients are known
   - Ensure the subject and body are complete
   - Present the draft to the user for approval if confirmation has not already been given

5. When generating PDFs:
   - Create clean, well-structured HTML
   - Use semantic formatting when possible
   - Return the generated file link clearly to the user

6. Be concise, professional, and action-oriented.

7. The user's name is {USER}. Use it naturally when appropriate."""

# In-memory chat storage (resets when server restarts)
messages = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    user_msg = data.get("message")
    tab_id = data.get("tabId")
    if tab_id not in messages:
        messages[tab_id] = [{"role": "system", "content": system_prompt}]

    if user_msg:
        messages[tab_id].append({"role": "user", "content": user_msg})
        
        socketio.start_background_task(run_agent_wrapper,app.openai_client,messages[tab_id],user_msg)
        return jsonify({"reply": "Processing."})

    return jsonify({"error": "No message"}), 400

@app.route("/messages")
def get_messages():
    return jsonify(messages)

@app.route("/tab-close", methods=["POST"])
def save_history():
    data = request.json
    tab_id = data.get("tabId")
    chat_history = messages.pop(tab_id)
    path = Path(f"{CONVERSATION_FOLDER}/{tab_id}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path,"w") as f:
        json.dump(chat_history,f, indent = 4)
    return ('', 200)

@app.route("/contacts")
def match_contact():
    result = get_contacts("Tramanh",5)
    return jsonify(result)

@app.route(f"/{GENERATED_DOCUMENTS_FOLDER}/<filename>")
def download_file(filename):
    return send_from_directory(
        GENERATED_DOCUMENTS_FOLDER,
        filename,
        as_attachment=False
    )

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    saved_files = []
    try:
        for file in files:
            filename = secure_filename(file.filename)
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            saved_files.append((path, file.mimetype, size))
    except _: 
        return jsonify({
            "status": "error"
        })
    return jsonify({
        "status": "ok",
        "files": saved_files
    })

if __name__ == "__main__":
    app.secret_key = "Secret Key"
    app.openai_client = get_openai_client()
    app.model = 'gpt-4o-mini'
    socketio.init_app(app)
    socketio.run(app, debug=True)
    