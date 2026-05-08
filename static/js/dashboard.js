const cameraFeed = document.getElementById("camera-feed");
const cameraStatus = document.getElementById("camera-status");
const eventsList = document.getElementById("events-list");

function refreshFrame() {
    const next = new Image();
    next.onload = () => {
        cameraFeed.src = next.src;
        cameraStatus.innerHTML = '<span class="status-dot active"></span>Câmera ativa';
        cameraStatus.className = "text-success";
    };
    next.onerror = () => {
        cameraStatus.innerHTML = '<span class="status-dot inactive"></span>Aguardando câmera...';
        cameraStatus.className = "text-danger";
    };
    next.src = "/frame?t=" + Date.now();
}

function renderEvents(events) {
    if (!events.length) {
        eventsList.innerHTML = '<p class="no-events">Nenhuma detecção registrada ainda.</p>';
        return;
    }
    eventsList.innerHTML = events.map(e => `
        <div class="event-card card mb-2">
            <div class="card-body d-flex align-items-center gap-3">
                <img
                    src="${e.image_path}"
                    alt="${e.label}"
                    class="event-thumb"
                    onerror="this.style.display='none'"
                >
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
        const res = await fetch("/events");
        const events = await res.json();
        renderEvents(events);
    } catch (_) {}
}

setInterval(refreshFrame, 200);
setInterval(refreshEvents, 3000);
