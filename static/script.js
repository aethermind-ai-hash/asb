document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // NOTIFICATION MODULE
    // =========================
    const NotificationModule = (() => {
        function show(message, duration = 3000) {
            const container = document.getElementById("notification-container");
            if (!container) return;

            const notif = document.createElement("div");
            notif.className = "notification";
            notif.textContent = message;
            container.appendChild(notif);

            notif.offsetHeight; // force reflow
            notif.classList.add("show");

            setTimeout(() => {
                notif.classList.remove("show");
                notif.classList.add("hide");
                notif.addEventListener("transitionend", () => notif.remove());
            }, duration);
        }

        return { show };
    })();

    // =========================
    // TYPING MODULE
    // =========================
    const TypingModule = (() => {
        async function type(container, message, speed = 30) {
            container.textContent = "";
            for (let i = 0; i < message.length; i++) {
                container.textContent += message[i];
                container.scrollIntoView({ behavior: "smooth", block: "end" });
                await new Promise(resolve => setTimeout(resolve, speed));
            }
        }

        return { type };
    })();

    // =========================
    // MENU MODULE
    // =========================
    const MenuModule = (() => {
        const menuBtn = document.getElementById("menu-btn");
        const menu = document.getElementById("menu");
        const overlay = document.getElementById("menu-overlay");
        const menuLinks = document.querySelectorAll("#menu a[data-tab]");

        function init() {
            const accButtons = document.querySelectorAll("#menu .accordion");
            accButtons.forEach(button => {
                button.addEventListener("click", () => {
                    const submenu = button.nextElementSibling;
                    document.querySelectorAll("#menu .submenu").forEach(sm => sm !== submenu && sm.classList.remove("active"));
                    document.querySelectorAll("#menu .accordion").forEach(btn => btn !== button && btn.classList.remove("active"));
                    submenu.classList.toggle("active");
                    button.classList.toggle("active");
                });
            });

            menuBtn?.addEventListener("click", () => {
                menu.classList.toggle("open");
                menuBtn.classList.toggle("active");
                overlay.classList.toggle("show");
            });

            overlay?.addEventListener("click", () => {
                menu.classList.remove("open");
                menuBtn.classList.remove("active");
                overlay.classList.remove("show");
            });

            menuLinks.forEach(link => {
                link.addEventListener("click", (e) => {
                    e.preventDefault();
                    const tab = link.dataset.tab;
                    menu.classList.remove("open");
                    overlay.classList.remove("show");
                    document.querySelectorAll(".tab-content").forEach(tc => tc.classList.add("hidden"));
                    const activeTab = document.getElementById(tab);
                    activeTab?.classList.remove("hidden");
                });
            });
        }

        return { init };
    })();

    // =========================
    // NAV & TAB MODULE
    // =========================
    const NavModule = (() => {
        function init() {
            const navButtons = document.querySelectorAll(".nav-btn");
            const tabContents = document.querySelectorAll(".tab-content");

            navButtons.forEach(btn => {
                btn.addEventListener("click", () => {
                    navButtons.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    tabContents.forEach(tab => tab.classList.add("hidden"));
                    const target = document.getElementById(btn.dataset.tab);
                    target?.classList.remove("hidden");
                });
            });
        }

        return { init };
    })();

    // =========================
    // MODAL MODULE
    // =========================
    const ModalModule = (() => {
        const modals = document.querySelectorAll(".modal-overlay");

        function open(modalId) {
            modals.forEach(m => m.classList.remove("show"));
            const modal = document.getElementById(modalId);
            modal?.classList.add("show");
        }

        function close(modal) {
            modal?.classList.remove("show");
        }

        function init() {
            document.querySelectorAll(".close-btn").forEach(btn => {
                btn.addEventListener("click", () => close(btn.closest(".modal-overlay")));
            });

            modals.forEach(modal => {
                modal.addEventListener("click", e => {
                    if (e.target === modal) close(modal);
                });
            });
        }

        return { init, open, close };
    })();

    // =========================
    // FAQ MODULE
    // =========================
    const FaqModule = (() => {
        let faq = {};
        const resultsDiv = document.getElementById("faq-results");
        const searchInput = document.getElementById("search-input");

        async function loadFaq() {
            try {
                const res = await fetch("/faq_data");
                if (res.ok) {
                    faq = await res.json();
                    renderResults(faq);
                }
            } catch (err) {
                console.error(err);
                NotificationModule.show("Failed to load FAQs.");
            }
        }

        function renderResults(filteredFaq) {
            if (!resultsDiv) return;
            resultsDiv.innerHTML = "";

            if (!filteredFaq || Object.keys(filteredFaq).length === 0) {
                resultsDiv.innerHTML = "<p class='no-results'>No matching questions found.</p>";
                return;
            }

            const sortedQuestions = Object.keys(filteredFaq).sort((a, b) => {
                if (filteredFaq[a].popular && !filteredFaq[b].popular) return -1;
                if (!filteredFaq[a].popular && filteredFaq[b].popular) return 1;
                return a.localeCompare(b);
            });

            sortedQuestions.forEach(q => {
                const info = filteredFaq[q];
                const card = document.createElement("div");
                card.className = "faq-card";
                card.innerHTML = `
                    <h3>${q}</h3>
                    <p>${info.answer}</p>
                    <div class="faq-toggle-wrapper">
                        <label class="switch">
                            <input type="checkbox" class="faq-popular-toggle" data-question="${q}" ${info.popular ? "checked" : ""}>
                            <span class="slider"></span>
                        </label>
                        <span class="badge ${info.popular ? "badge-popular" : "badge-normal"}">
                            ${info.popular ? "Popular" : "Normal"}
                        </span>
                        <button class="delete-faq" data-question="${q}">Delete</button>
                    </div>
                `;
                resultsDiv.appendChild(card);
            });
        }

        function init() {
            const viewFaqBtn = document.getElementById("view-faq-btn");

            viewFaqBtn?.addEventListener("click", async () => {
                ModalModule.open("faq-modal");
                await loadFaq();
            });

            searchInput?.addEventListener("input", () => {
                const query = searchInput.value.toLowerCase();
                const filtered = {};
                for (const q in faq) if (q.toLowerCase().includes(query)) filtered[q] = faq[q];
                renderResults(filtered);
            });
        }

        return { init, loadFaq, renderResults };
    })();

    // =========================
    // CHAT MODULE
    // =========================
    const ChatModule = (() => {
        const chatForm = document.getElementById("chat-form");
        const chatInput = document.getElementById("chat-input");
        const chatContainer = document.getElementById("chat-box");

        function displayBotMessage(msg) {
            const botDiv = document.createElement("div");
            botDiv.className = "bot-message";
            chatContainer.appendChild(botDiv);
            return TypingModule.type(botDiv, msg);
        }

        async function init() {
            if (chatContainer) {
                displayBotMessage("Hello! I'm AetherMind Smart FAQ Assistant 🤖. Ask me anything from the popular questions below or type your own question!");
            }

            if (!chatForm || !chatInput || !chatContainer) return;

            chatForm.addEventListener("submit", async e => {
                e.preventDefault();
                const userMessage = chatInput.value.trim();
                if (!userMessage) return;

                const userDiv = document.createElement("div");
                userDiv.className = "user-message";
                userDiv.textContent = userMessage;
                chatContainer.appendChild(userDiv);
                chatInput.value = "";

                try {
                    const res = await fetch("/get_bot_response", {
                        method: "POST",
                        body: JSON.stringify({ message: userMessage }),
                        headers: { "Content-Type": "application/json" },
                    });
                    const data = await res.json();
                    await displayBotMessage(data.response);
                } catch (err) {
                    console.error(err);
                    await displayBotMessage("Sorry, something went wrong.");
                }
            });
        }

        return { init };
    })();

    // =========================
    // INIT ALL MODULES
    // =========================
    MenuModule.init();
    NavModule.init();
    ModalModule.init();
    FaqModule.init();
    ChatModule.init();
});
