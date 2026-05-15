// ── State ─────────────────────────────────────────────────────────────────────
const chatHistory = [];

// ── Camera status ─────────────────────────────────────────────────────────────
const cameraStatus = document.getElementById("camera-status");

async function refreshCameraStatus() {
    try {
        const res  = await fetch("/camera/status");
        const data = await res.json();
        if (data.online && data.has_live_frame) {
            cameraStatus.innerHTML  = '<span class="status-dot active"></span>Câmera ativa';
            cameraStatus.className  = "text-success";
        } else {
            cameraStatus.innerHTML  = '<span class="status-dot inactive"></span>Aguardando câmera...';
            cameraStatus.className  = "text-danger";
        }
    } catch (_) {
        cameraStatus.innerHTML = '<span class="status-dot inactive"></span>Sem conexão';
        cameraStatus.className = "text-danger";
    }
}

// ── Events ────────────────────────────────────────────────────────────────────
const eventsList = document.getElementById("events-list");

function renderEvents(events) {
    if (!events.length) {
        eventsList.innerHTML = '<p class="no-events">Nenhuma detecção registrada ainda.</p>';
        return;
    }
    eventsList.innerHTML = events.map(e => `
        <div class="event-card card mb-2">
            <div class="card-body d-flex align-items-center gap-3">
                <img src="${e.image_path}" alt="${e.label}" class="event-thumb"
                     onerror="this.style.display='none'">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="event-label">${e.label}</span>
                        <span class="badge-conf">${Math.round(e.confidence * 100)}%</span>
                    </div>
                    <div class="event-meta mt-1">${e.event_time}</div>
                </div>
            </div>
        </div>
    `).join("");
}

async function refreshEvents() {
    try {
        const res    = await fetch("/events");
        const events = await res.json();
        renderEvents(events);
    } catch (_) {}
}

// ── Chat ──────────────────────────────────────────────────────────────────────
const chatHistoryEl = document.getElementById("chat-history");
const chatInput     = document.getElementById("chat-input");
const chatSendBtn   = document.getElementById("chat-send-btn");

function appendBubble(role, text) {
    const div = document.createElement("div");
    div.className = `chat-bubble ${role}`;
    div.textContent = text;
    chatHistoryEl.appendChild(div);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
    return div;
}

function setInputEnabled(enabled) {
    chatInput.disabled    = !enabled;
    chatSendBtn.disabled  = !enabled;
}

async function sendMessage() {
    const question = chatInput.value.trim();
    if (!question) return;

    chatInput.value = "";
    setInputEnabled(false);

    appendBubble("user", question);
    const assistantBubble = appendBubble("assistant typing", "...");

    let fullResponse = "";

    try {
        const res = await fetch("/chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ question, history: chatHistory }),
        });

        const reader  = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            fullResponse += decoder.decode(value, { stream: true });
            assistantBubble.textContent = fullResponse;
            chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
        }

        assistantBubble.classList.remove("typing");
        chatHistory.push({ role: "user",      content: question      });
        chatHistory.push({ role: "assistant", content: fullResponse  });

    } catch (err) {
        assistantBubble.textContent = "[Erro ao conectar com o agente.]";
        assistantBubble.classList.remove("typing");
    }

    setInputEnabled(true);
    chatInput.focus();
}

chatSendBtn.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ── Init ──────────────────────────────────────────────────────────────────────
refreshCameraStatus();
refreshEvents();
setInterval(refreshCameraStatus, 5000);
setInterval(refreshEvents, 3000);
