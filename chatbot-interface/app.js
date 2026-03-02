// Configuration for API
const API_BASE_URL = 'http://localhost:8000/api/v1';
let currentClient = null;

// UI Elements
const chatWindow = document.getElementById('chat-window');
const chatToggleBtn = document.getElementById('chat-toggle');
const closeBtn = document.getElementById('close-chat-btn');
const restartBtn = document.getElementById('restart-btn');
const messagesContainer = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInputBox = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let currentState = 'start';
let isTyping = false;

// Helpers
const scrollToBottom = () => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

const showTyping = () => {
    isTyping = true;
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'typing-indicator message-wrapper bot';
    typingDiv.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

const removeTyping = () => {
    isTyping = false;
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

const addMessage = (text, sender, delay = 500) => {
    return new Promise((resolve) => {
        if (sender === 'bot') showTyping();

        setTimeout(() => {
            if (sender === 'bot') removeTyping();

            const msgDiv = document.createElement('div');
            msgDiv.className = `message-wrapper ${sender}`;
            msgDiv.innerHTML = `<div class="message ${sender}">${text}</div>`;
            messagesContainer.appendChild(msgDiv);
            scrollToBottom();
            resolve();
        }, delay);
    });
}

const addOptions = (options) => {
    const optsDiv = document.createElement('div');
    optsDiv.className = 'message-wrapper bot options-container';

    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'quick-reply-btn';
        btn.textContent = opt.text;
        btn.onclick = () => handleOptionClick(opt);
        optsDiv.appendChild(btn);
    });

    messagesContainer.appendChild(optsDiv);
    scrollToBottom();
}

const addEndState = (endInfo) => {
    const endDiv = document.createElement('div');
    endDiv.className = `flow-status ${endInfo.type}`;
    endDiv.textContent = endInfo.text;
    messagesContainer.appendChild(endDiv);
    scrollToBottom();

    userInputBox.disabled = true;
    sendBtn.disabled = true;
    userInputBox.placeholder = "Chat finalizado. Usa el botón de reinicio para volver a empezar.";
}

const disableInput = () => {
    userInputBox.disabled = true;
    sendBtn.disabled = true;
}

const enableInput = (placeholder = "Escribe tu mensaje...") => {
    userInputBox.disabled = false;
    sendBtn.disabled = false;
    userInputBox.placeholder = placeholder;
    userInputBox.focus();
}

// API Calls
async function fetchClientByDocOrPhone(input) {
    try {
        let res = await fetch(`${API_BASE_URL}/clients/by-document/${input}`);
        let json = await res.json();
        if (json.type === "success" && json.data) return json.data;

        res = await fetch(`${API_BASE_URL}/clients/by-phone/${input}`);
        json = await res.json();
        if (json.type === "success" && json.data) return json.data;
        return null;
    } catch (error) {
        console.error("API error:", error);
        return null;
    }
}

async function resolveClient(name, address, price) {
    try {
        const res = await fetch(`${API_BASE_URL}/clients/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, address, internet_plan_price: parseFloat(price) })
        });
        const json = await res.json();
        return json.type === "success" ? json.data : null;
    } catch (error) {
        console.error("Resolve error:", error);
        return null;
    }
}

async function updateClientData(serviceId, doc, phone) {
    try {
        const res = await fetch(`${API_BASE_URL}/clients/${serviceId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document: doc, phone: phone })
        });
        const json = await res.json();
        return json.type === "success";
    } catch (error) {
        console.error("Update error:", error);
        return false;
    }
}

async function checkZoneBlocked(zoneId) {
    try {
        const res = await fetch(`${API_BASE_URL}/tickets/zone-blocked/${zoneId}`);
        const json = await res.json();
        return json.type === "success" ? json.data.is_blocked : false;
    } catch (error) {
        console.error("Zone check error:", error);
        return false;
    }
}

async function startPing(serviceId) {
    try {
        const res = await fetch(`${API_BASE_URL}/${serviceId}/ping/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pings: 4 })
        });
        const json = await res.json();
        return json.type === "success" ? json.data.task_id : null;
    } catch (error) {
        console.error("Ping start error:", error);
        return null;
    }
}

async function pollPingResult(taskId) {
    try {
        // We might need to wait a bit as pings take time.
        const maxAttempts = 5;
        for (let i = 0; i < maxAttempts; i++) {
            await new Promise(r => setTimeout(r, 2000));
            const res = await fetch(`${API_BASE_URL}/ping/${taskId}/`);
            const json = await res.json();
            if (json.type === "success") return "stable";
            if (json.action === "no_internet") return "no_internet";
            if (json.action === "intermittent_connection") return "intermittent";
        }
        return "failed";
    } catch (error) {
        console.error("Ping poll error:", error);
        return "failed";
    }
}

async function createTicket() {
    try {
        const res = await fetch(`${API_BASE_URL}/tickets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                service_id: currentClient.service_id,
                zone_id: currentClient.zone_id,
                subject: "Avería reportada por Chatbot",
                description: `Soporte automático: Problema de conexión detectado tras diagnóstico físico y de red.`,
                technician_id: currentClient.technician_id || 1
            })
        });
        const json = await res.json();
        if (json.type === "success") return "success";
        if (json.action === "zone_ticket_limit_reached") return "limit";
        return "error";
    } catch (error) {
        console.error("API error:", error);
        return "error";
    }
}

// State Variables for Resolve/Update Flow
let resolveData = { name: '', address: '', price: '' };
let updateData = { doc: '', phone: '' };

const processState = async (stateKey, input = null) => {
    currentState = stateKey;
    disableInput();

    switch (stateKey) {
        case 'start':
            await addMessage("¡Hola! Bienvenido. ¿En qué podemos ayudarte hoy?", 'bot', 500);
            enableInput("Describe tu problema o duda...");
            break;

        case 'detect_intent':
            const lowerInput = input.toLowerCase();
            if (lowerInput.includes('agente')) {
                await addMessage("Entendido. Te derivaré con un agente humano para atenderte mejor.", 'bot');
                addEndState({ text: "🔵 Derivación directa a Agente - FIN", type: "blue" });
                return;
            }

            const helpKeywords = ['soporte', 'ayuda', 'internet', 'falla', 'avería', 'lento', 'caído', 'luz roja', 'sin servicio'];
            const seeksSupport = helpKeywords.some(k => lowerInput.includes(k));

            if (seeksSupport) {
                await addMessage("Entiendo que necesitas soporte técnico. Por favor, ingresa tu <strong>Cédula</strong> o el <strong>Teléfono</strong> registrado.", 'bot');
                enableInput("Ej: 12345678");
                currentState = 'ask_id';
            } else {
                await addMessage("¿Ya eres cliente nuestro?", 'bot');
                addOptions([
                    { text: "Sí", action: "ask_id" },
                    { text: "No", action: "ask_resolve_name" }
                ]);
            }
            break;

        case 'ask_id':
            await addMessage("Por favor, ingresa tu <strong>Documento</strong> o <strong>Teléfono</strong>.", 'bot');
            enableInput();
            break;

        case 'process_id':
            showTyping();
            currentClient = await fetchClientByDocOrPhone(input);
            removeTyping();

            if (currentClient) {
                await processState('check_debt_diagnostic');
            } else {
                await addMessage("No te encontré con esos datos. Vamos a intentarlo de otra forma.", 'bot');
                await processState('ask_resolve_name');
            }
            break;

        case 'check_debt_diagnostic':
            await addMessage(`¡Hola <strong>${currentClient.name}</strong>! Revisando el estado de tu cuenta...`, 'bot');
            if (currentClient.outstanding_balance > 0) {
                await addMessage(`Detectamos un saldo pendiente de <strong>$${currentClient.outstanding_balance}</strong>. Por favor, regulariza tu pago para continuar. ¡Buen día!`, 'bot');
                addEndState({ text: "🟠 Deuda detectada - FIN", type: "orange" });
            } else {
                await processState('check_massive_failure');
            }
            break;

        case 'check_massive_failure':
            showTyping();
            const isBlocked = await checkZoneBlocked(currentClient.zone_id);
            removeTyping();

            if (isBlocked) {
                await addMessage("En este momento tenemos una falla masiva reportada en tu zona. Nuestro equipo técnico ya está trabajando para solucionarlo. ¡Gracias por tu paciencia!", 'bot');
                addEndState({ text: "🔴 Falla masiva en zona - FIN", type: "red" });
            } else {
                await addMessage("¿Tu router tiene alguna <strong>luz roja</strong> encendida?", 'bot');
                addOptions([
                    { text: "Sí, tiene luz roja", action: "router_red_light" },
                    { text: "No, todo normal", action: "initiate_ping" }
                ]);
            }
            break;

        case 'router_red_light':
            await addMessage("Por favor, apaga el router, espera 10 segundos y vuélvelo a encender.", 'bot');
            await addMessage("¿La luz roja se quitó?", 'bot', 2000);
            addOptions([
                { text: "Sí, ya funciona", action: "service_restored" },
                { text: "No, sigue roja", action: "initiate_ping" }
            ]);
            break;

        case 'service_restored':
            await addMessage("¡Qué bueno que se solucionó! Gracias por contactarnos.", 'bot');
            addEndState({ text: "🟢 Servicio restaurado tras reinicio - FIN", type: "green" });
            break;

        case 'initiate_ping':
            await addMessage("Realizaremos una prueba de conexión remota. Esto tardará unos segundos...", 'bot');
            showTyping();
            const taskId = await startPing(currentClient.service_id);
            if (!taskId) {
                removeTyping();
                await processState('create_ticket_auto');
                return;
            }
            const pingResult = await pollPingResult(taskId);
            removeTyping();

            if (pingResult === "stable") {
                await addMessage("Tu conexión parece estar estable desde nuestro lado. Si el problema persiste, revisa tus cables internos.", 'bot');
                addEndState({ text: "🟢 Conexión estable (Ping OK) - FIN", type: "green" });
            } else {
                await addMessage(`Tu conexión se encuentra: <strong>${pingResult === 'no_internet' ? 'Sin Internet' : 'Intermitente'}</strong>.`, 'bot');
                await processState('create_ticket_auto');
            }
            break;

        case 'create_ticket_auto':
            showTyping();
            const res = await createTicket();
            removeTyping();
            if (res === "success") {
                await addMessage("He generado un ticket de soporte para que un técnico revise tu caso. Te contactaremos pronto.", 'bot');
                addEndState({ text: "🟢 Ticket automático creado - FIN", type: "green" });
            } else if (res === "limit") {
                await addMessage("Ya tenemos reportes activos en tu zona. Estamos trabajando en ello.", 'bot');
                addEndState({ text: "🟠 Límite de reportes - FIN", type: "orange" });
            } else {
                await addMessage("No pude generar el ticket automáticamente. Te derivaré con un asesor.", 'bot');
                addEndState({ text: "🔴 Derivación a asesor - FIN", type: "red" });
            }
            break;

        // --- RESOLVE FLOW ---
        case 'ask_resolve_name':
            await addMessage("Para buscarte, por favor dime tu <strong>Nombre Completo</strong>.", 'bot');
            enableInput();
            break;
        case 'ask_resolve_address':
            resolveData.name = input;
            await addMessage("Dime tu <strong>Dirección</strong> exacta.", 'bot');
            enableInput();
            break;
        case 'ask_resolve_price':
            resolveData.address = input;
            await addMessage("¿Cuál es el <strong>Precio</strong> mensual de tu plan?", 'bot');
            enableInput("Ej: 40000");
            break;
        case 'process_resolve':
            resolveData.price = input;
            showTyping();
            currentClient = await resolveClient(resolveData.name, resolveData.address, resolveData.price);
            removeTyping();

            if (currentClient) {
                await addMessage(`¡Te encontré! Eres <strong>${currentClient.name}</strong>.`, 'bot');
                await addMessage("¿Deseas actualizar tu Cédula y Teléfono en nuestro sistema para futuras consultas?", 'bot');
                addOptions([
                    { text: "Sí", action: "ask_update_doc" },
                    { text: "No, continuar diagnóstico", action: "check_debt_diagnostic" }
                ]);
            } else {
                await addMessage("Lo siento, no pude encontrarte con esos datos. Te derivaré con un asesor.", 'bot');
                addEndState({ text: "🔴 Cliente no encontrado (Resolve fail) - FIN", type: "red" });
            }
            break;

        case 'ask_update_doc':
            await addMessage("Dime tu número de <strong>Cédula</strong>.", 'bot');
            enableInput();
            break;
        case 'ask_update_phone':
            updateData.doc = input;
            await addMessage("Dime tu número de <strong>Teléfono</strong>.", 'bot');
            enableInput();
            break;
        case 'process_update':
            updateData.phone = input;
            showTyping();
            const updated = await updateClientData(currentClient.service_id, updateData.doc, updateData.phone);
            removeTyping();
            if (updated) await addMessage("¡Datos actualizados con éxito!", 'bot');
            else await addMessage("No pude actualizar los datos, pero continuaremos con el soporte.", 'bot');
            await processState('check_debt_diagnostic');
            break;
    }
}

const handleOptionClick = async (option) => {
    if (isTyping) return;

    const optionContainers = document.querySelectorAll('.options-container');
    optionContainers.forEach(container => container.remove());

    await addMessage(option.text, 'user', 0);
    processState(option.action);
}

// Event Listeners
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isTyping) return;

    const text = userInputBox.value.trim();
    if (!text) return;

    userInputBox.value = '';
    disableInput();

    await addMessage(text, 'user', 0);

    if (currentState === 'start') {
        processState('detect_intent', text);
    } else if (currentState === 'ask_id') {
        processState('process_id', text);
    } else if (currentState === 'ask_resolve_name') {
        processState('ask_resolve_address', text);
    } else if (currentState === 'ask_resolve_address') {
        processState('ask_resolve_price', text);
    } else if (currentState === 'ask_resolve_price') {
        processState('process_resolve', text);
    } else if (currentState === 'ask_update_doc') {
        processState('ask_update_phone', text);
    } else if (currentState === 'ask_update_phone') {
        processState('process_update', text);
    }
});

chatToggleBtn.addEventListener('click', () => {
    chatWindow.classList.add('show');
    chatToggleBtn.classList.add('hidden');
    if (currentState === 'start' && !currentClient) {
        processState('start');
    }
});

closeBtn.addEventListener('click', () => {
    chatWindow.classList.remove('show');
    chatToggleBtn.classList.remove('hidden');
});

restartBtn.addEventListener('click', () => {
    messagesContainer.innerHTML = '';
    userInputBox.value = '';
    currentClient = null;
    processState('start');
});

// Auto-start for quick testing after loaded
window.addEventListener('load', () => {
    setTimeout(() => {
        chatToggleBtn.click();
    }, 500);
});
