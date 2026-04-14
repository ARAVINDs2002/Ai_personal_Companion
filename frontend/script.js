const API_URL = "http://localhost:8000";

const setupContainer = document.getElementById("setup-container");
const chatContainer = document.getElementById("chat-container");

// Setup UI
const setupBtn = document.getElementById("setup-btn");
const setupError = document.getElementById("setup-error");
const uNameInput = document.getElementById("setup-user-name");
const uGenderInput = document.getElementById("setup-user-gender");
const aNameInput = document.getElementById("setup-ai-name");
const aGenderInput = document.getElementById("setup-ai-gender");

// Chat UI
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const chatArea = document.getElementById("chat-area");
const chatAiNameDisplay = document.getElementById("chat-ai-name-display");
const headerAvatarInitial = document.getElementById("header-avatar-initial");

let isProcessing = false;
let currentAiName = "Maya";

async function checkProfile() {
    try {
        const res = await fetch(`${API_URL}/profile`);
        if (res.ok) {
            const data = await res.json();
            if (data.is_setup) {
                transitionToChat();
            }
        }
    } catch (e) {
        console.error("Backend not running or unreachable:", e);
    }
}

function transitionToChat() {
    setupContainer.classList.add("hidden");
    
    // Slight delay to allow opacity transition
    setTimeout(() => {
        chatContainer.classList.remove("hidden");
        chatInput.focus();
    }, 400);
}

setupBtn.addEventListener("click", async () => {
    const un = uNameInput.value.trim();
    const ug = uGenderInput.value.trim();
    const an = aNameInput.value.trim();
    const ag = aGenderInput.value.trim();

    if (!un || !ug || !an || !ag) {
        setupError.textContent = "All fields are required and cannot be empty spaces.";
        return;
    }
    
    setupBtn.disabled = true;
    setupError.textContent = "";
    setupBtn.textContent = "Saving...";

    try {
        const res = await fetch(`${API_URL}/setup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_name: un,
                user_gender: ug,
                ai_name: an,
                ai_gender: ag
            })
        });

        if (res.ok) {
            currentAiName = an;
            chatAiNameDisplay.textContent = an;
            headerAvatarInitial.textContent = an.charAt(0).toUpperCase();
            transitionToChat();
        } else {
            const err = await res.json();
            setupError.textContent = err.detail || "Error saving profile.";
            setupBtn.disabled = false;
            setupBtn.textContent = "Start Chatting";
        }
    } catch (e) {
        setupError.textContent = "Network error. Is the backend running?";
        setupBtn.disabled = false;
        setupBtn.textContent = "Start Chatting";
    }
});

chatInput.addEventListener("input", () => {
    sendBtn.disabled = isProcessing || chatInput.value.trim() === "";
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !sendBtn.disabled) {
        sendMessage();
    }
});

sendBtn.addEventListener("click", () => {
    if (!sendBtn.disabled) {
        sendMessage();
    }
});

function appendMessage(text, sender) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", sender);
    
    if (sender === "ai") {
        const avatar = document.createElement("div");
        avatar.classList.add("msg-avatar");
        avatar.textContent = currentAiName.charAt(0).toUpperCase();
        wrapper.appendChild(avatar);
    }
    
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    msgDiv.textContent = text;
    wrapper.appendChild(msgDiv);
    
    chatArea.appendChild(wrapper);
    scrollToBottom();
}

function appendTypingIndicator() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", "ai");
    wrapper.id = "typing-indicator-wrapper";
    
    const avatar = document.createElement("div");
    avatar.classList.add("msg-avatar");
    avatar.textContent = currentAiName.charAt(0).toUpperCase();
    wrapper.appendChild(avatar);
    
    const indicator = document.createElement("div");
    indicator.classList.add("typing-indicator");
    indicator.innerHTML = `<span></span><span></span><span></span>`;
    wrapper.appendChild(indicator);
    
    chatArea.appendChild(wrapper);
    scrollToBottom();
}

function removeTypingIndicator() {
    const wrapper = document.getElementById("typing-indicator-wrapper");
    if (wrapper) {
        wrapper.remove();
    }
}

function scrollToBottom() {
    chatArea.scrollTo({
        top: chatArea.scrollHeight,
        behavior: 'smooth'
    });
}

async function sendMessage() {
    const msgText = chatInput.value.trim();
    if (!msgText) return;

    // UI Updates
    chatInput.value = "";
    sendBtn.disabled = true;
    isProcessing = true;
    
    appendMessage(msgText, "user");
    appendTypingIndicator();

    try {
        const res = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msgText })
        });
        
        removeTypingIndicator();

        if (res.ok) {
            const data = await res.json();
            appendMessage(data.reply, "ai");
        } else {
            const err = await res.json();
            appendMessage(err.detail || "Something went wrong...", "ai");
        }
    } catch (e) {
        removeTypingIndicator();
        appendMessage("Hey… I'm having a small issue connecting right now, but I'm here with you 🙂", "ai");
    } finally {
        isProcessing = false;
        if (chatInput.value.trim() !== "") {
            sendBtn.disabled = false;
        }
        chatInput.focus();
    }
}

function resetChat() {
    fetch(`${API_URL}/reset`, {
        method: "POST"
    })
    .then(() => {
        location.reload();
    });
}

// Init
checkProfile();
