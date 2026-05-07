if (!sessionStorage.getItem("tab_id")) {
    sessionStorage.setItem("tab_id", crypto.randomUUID());
}

const tabId = sessionStorage.getItem("tab_id");

const textarea = document.getElementById("message");
textarea.addEventListener("input", () => {
    textarea.style.height = "0px";            
    textarea.style.height = textarea.scrollHeight + "px";
});

function checkEnter(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}

const socket = io();
socket.on("show_popup", (data) => {
    const result = confirm(data.message);
    socket.emit("popup_response", {
        id: data.requestId,
        answer: result ? "yes" : "no"
    });
});

socket.on("bot-reply", (data) => {
    appendMessage("bot", data.reply);
});

async function sendMessage() {
    const input = document.getElementById("message");
    const msg = input.value;

    textarea.style.height = "auto";
    input.value = "";

    if (!msg) return;
    appendMessage("user", msg);

    const response = await fetch("/send", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: msg,
            tabId: tabId
        })
    });

    const data = await response.json();    
}

function formatContent(content) {
    if (!content) return "";
    return marked.parse(content);
}

function appendMessage(sender, text) {
    const chat = document.getElementById("chat");
    const div = document.createElement("div");
    const msgContainer = document.createElement("div");
    msgContainer.className = "message-row " + sender;
    div.className = "message-bubble";
    div.innerHTML = formatContent(text);
    msgContainer.appendChild(div);
    chat.appendChild(msgContainer);
    chat.scrollTop = chat.scrollHeight;
}

const dropZone = document.getElementById("input-area");

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault(); // 🔑 required to allow drop
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");

    const files = e.dataTransfer.files;

    if (files.length > 0) {
        handleFiles(files);
    }
});

function handleFiles(files) {
    for (let file of files) {
        console.log("Dropped file:", file.name);

        appendMessage("user", `📎 ${file.name}`);
    }

}

window.addEventListener("beforeunload", function () {
    const data = JSON.stringify({
        tabId: tabId
    });

    const blob = new Blob([data], {
        type: "application/json"
    });

    navigator.sendBeacon("/tab-close", blob);
});