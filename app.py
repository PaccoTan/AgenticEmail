import json
from flask import Flask, render_template, request, jsonify
from agent import get_openai_client, run_agent
from flask import session
import uuid

app = Flask(__name__)
system_prompt = """You are a helpful email assistant with access to tools. 
When the user asks you to do something, use the appropriate tool(s) to help them.
Available tools:
- generate_email: Create a simple email message and displays a preview to the user. Does not send the message.
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
        
        bot_reply = f"{run_agent(app.model,messages[tab_id],user_msg)}"
        return jsonify({"reply": bot_reply})

    return jsonify({"error": "No message"}), 400

@app.route("/messages")
def get_messages():
    print(messages)
    return jsonify(messages)

@app.route("/tab-close", methods=["POST"])
def save_history():
    data = request.json
    print(data)
    tab_id = data.get("tabId")
    with open(f"conversatins/{tab_id}.json","w") as f:
        f.write(json.dumps(messages))
    print(tab_id)

if __name__ == "__main__":
    app.secret_key = "Secret Key"
    app.model = get_openai_client()
    app.run(debug=True)
    