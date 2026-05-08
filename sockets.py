from extensions import socketio
pending = {}

@socketio.on("popup_response")
def handle_popup_response(data):
    request_id = data["id"]
    answer = data["answer"]
    if request_id in pending:
        pending[request_id]["answer"] = answer
        pending[request_id]["event"].set()