document.addEventListener("DOMContentLoaded", () => {
    // =========================
    // Chat Integration (with typing)
    // =========================
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatContainer = document.getElementById("chat-box"); // matches HTML



    // Default welcome fallback
    const DEFAULT_WELCOME =
        "Hello! I'm AetherMind Smart FAQ Assistant 🤖. Ask me anything from the popular questions below or type your own question!";

    async function loadWelcomeMessage() {
        try {
            const res = await fetch("/welcome_message");
            if (!res.ok) throw new Error("Failed to fetch welcome message");
            const data = await res.json();

            // Use DB message if exists, else default
            const message = data.message || DEFAULT_WELCOME;

            // Insert into chat window
            displayBotMessage(message);

            // Also populate the Manage FAQ textarea (admin side)
            const welcomeInput = document.getElementById("welcome-message");
            if (welcomeInput) welcomeInput.value = message;

        } catch (err) {
            console.error("Error loading welcome message:", err);
            displayBotMessage(DEFAULT_WELCOME);
        }
    }

    async function typeMessage(container, message, speed = 30) {
        container.textContent = "";
        for (let i = 0; i < message.length; i++) {
            container.textContent += message[i];
            container.scrollIntoView({ behavior: "smooth", block: "end" });
            await new Promise(resolve => setTimeout(resolve, speed));
        }
    }

    function displayBotMessage(message) {
        if (!chatContainer) return;
        const botDiv = document.createElement("div");
        botDiv.className = "bot-message";
        chatContainer.appendChild(botDiv);
        typeMessage(botDiv, message);
    }

    // Initialize chat with welcome message (DB or default)
    if (chatContainer) {
        loadWelcomeMessage();
    }

    // Handle chat form submission
    if (chatForm && chatInput && chatContainer) {
        chatForm.addEventListener("submit", async e => {
            e.preventDefault();
            const userMessage = chatInput.value.trim();
            if (!userMessage) return;

            // User bubble
            const userDiv = document.createElement("div");
            userDiv.className = "user-message";
            userDiv.textContent = userMessage;
            chatContainer.appendChild(userDiv);
            chatInput.value = "";

            // Bot response
            try {
                const res = await fetch("/get_bot_response", {
                    method: "POST",
                    body: JSON.stringify({ message: userMessage }),
                    headers: { "Content-Type": "application/json" },
                });
                const data = await res.json();

                const botDiv = document.createElement("div");
                botDiv.className = "bot-message";
                chatContainer.appendChild(botDiv);

                await typeMessage(botDiv, data.response);
            } catch (err) {
                console.error(err);
                const botDiv = document.createElement("div");
                botDiv.className = "bot-message";
                chatContainer.appendChild(botDiv);
                await typeMessage(botDiv, "Sorry, something went wrong.");
            }
        });
    }


});
