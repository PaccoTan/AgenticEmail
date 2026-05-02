from flask import Flask, render_template, request, jsonify
from agent import get_openai_client, run_agent

app = Flask(__name__)

# In-memory chat storage (resets when server restarts)
messages = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    user_msg = data.get("message")

    if user_msg:
        messages.append({"sender": "user", "text": user_msg})
        
        bot_reply = f"{run_agent(app.model,user_msg)}"
        messages.append({"sender": "bot", "text": bot_reply})

        return jsonify({"reply": bot_reply})

    return jsonify({"error": "No message"}), 400

@app.route("/messages")
def get_messages():
    return jsonify(messages)

if __name__ == "__main__":
    app.model = get_openai_client()
    app.run(debug=True)
    