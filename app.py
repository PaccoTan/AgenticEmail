import json
from flask import Flask, render_template, request, jsonify
from extensions import socketio
from agent import get_openai_client, run_agent_wrapper
from flask import session
import sockets
import uuid

app = Flask(__name__)
system_prompt = """You are a helpful email assistant with access to tools. 
When the user asks you to do something, use the appropriate tool(s) to help them.
Available tools:
- generate_email: Create a simple email message. Does not send the message.
- send_email: Send the email message to the target recipients.

Always use tools when they can help the user accomplish their goal. 
Only send an email, when the user is satisfied with the preview.
The user's name is Pacco Tan."""


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
        
        socketio.start_background_task(run_agent_wrapper,app.model,messages[tab_id],user_msg)
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
    with open(f"conversations/{tab_id}.json","w") as f:
        f.write(json.dumps(chat_history, indent = 4))

if __name__ == "__main__":
    app.secret_key = "Secret Key"
    app.model = get_openai_client()
    socketio.init_app(app)
    socketio.run(app, debug=True)
    