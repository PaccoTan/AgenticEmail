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
        body: JSON.stringify({ message: msg })
    });

    const data = await response.json();
    appendMessage("bot", data.reply);
    
}

function appendMessage(sender, text) {
    const chat = document.getElementById("chat");
    const div = document.createElement("div");
    const msgContainer = document.createElement("div");
    msgContainer.className = "message-row " + sender;
    div.className = "message-bubble";
    div.textContent = text;
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