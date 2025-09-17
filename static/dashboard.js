// =====================
// DASHBOARD.JS
// =====================
document.addEventListener("DOMContentLoaded", () => {

  // -------------------------
  // VARIABLES
  // -------------------------
  const desktopTabs = document.querySelectorAll(".desktop-tabs a[data-tab]");
  const hamburger = document.getElementById("right-hamburger");
  const sidebar = document.getElementById("right-sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  const logoutBtnDesktop = document.getElementById("logout-btn");
const logoutBtnSidebar = document.getElementById("logout-btn-sidebar");
  const userNameElem = document.getElementById("user-name");
  const userPicElem = document.getElementById("user-pic");
  const tabs = document.querySelectorAll(".sidebar-nav a[data-tab]");
  const faqListDiv = document.getElementById("faq-list");
  const addFaqForm = document.getElementById("add-faq-form");
  const popularLabel = document.getElementById("popular-label");
  const faqQuestionInput = document.getElementById("faq-question");
  const faqAnswerInput = document.getElementById("faq-answer");
  const faqQuestionsUL = document.getElementById("faq-questions");
  const popularFaqsDiv = document.getElementById("popular-faqs");
  const welcomeMessageTA = document.getElementById("welcome-message");
  const saveWelcomeBtn = document.getElementById("save-welcome");
  const chatBox = document.getElementById("chat-box");
  const questionInput = document.getElementById("question-input");
  const askBtn = document.getElementById("ask-btn");
  const faqPopularCheckbox = document.getElementById("faq-popular");
  const viewFaqsBtn = document.getElementById("view-faqs-btn");

  const user = window.user;

  // Function to handle logout
  const handleLogout = () => {
    fetch("/user_logout")
      .then(res => {
        if (!res.ok) throw new Error("Logout failed");
        window.location.href = "/login";
      })
      .catch(err => console.error("Logout error:", err));
  };

  // Attach listeners if buttons exist
  [logoutBtnDesktop, logoutBtnSidebar].forEach(btn => {
    if (btn) btn.addEventListener("click", handleLogout);
  });
  // Update the label dynamically when toggle changes
faqPopularCheckbox.addEventListener("change", () => {
  popularLabel.textContent = faqPopularCheckbox.checked ? "Popular" : "Normal";
});
  // -------------------------
  // INITIALIZE USER INFO
  // -------------------------
  if (userNameElem) userNameElem.textContent = user.name || "User";
  if (userPicElem) userPicElem.src = user.picture || "/static/default_avatar.png";


  // -------------------------
  // DASHBOARD METRICS
  // -------------------------
  const totalInteractionsElem = document.getElementById("total-interactions");
  const activeUsersElem = document.getElementById("active-users");
  const faqUsageElem = document.getElementById("faq-usage");
  const remainingAIRequestsElem = document.getElementById("remaining-ai-requests");
  const newLeadsElem = document.getElementById("new-leads");

  // -------------------------
// SIDEBAR TOGGLE
// -------------------------
hamburger?.addEventListener("click", () => {
  if (window.innerWidth < 1024) { // only toggle on mobile
    hamburger.classList.toggle("active");
    sidebar.classList.toggle("open");
    overlay.classList.toggle("show");
  }
});

overlay?.addEventListener("click", () => {
  if (window.innerWidth < 1024) {
    hamburger.classList.remove("active");
    sidebar.classList.remove("open");
    overlay.classList.remove("show");
  }
});

// -------------------------
// TAB SWITCHING
// -------------------------
function showSection(tab) {
  document.querySelectorAll(".dashboard-section").forEach(sec => {
    sec.classList.add("hidden");
    sec.classList.remove("active");
  });

  const section = document.getElementById(tab);
  if (section) {
    section.classList.remove("hidden");
    section.classList.add("active");
  }

  // Remove active from all sidebar links
  tabs.forEach(link => link.classList.remove("active"));
  const activeLink = document.querySelector(`.sidebar-nav a[data-tab="${tab}"]`);
  if (activeLink) activeLink.classList.add("active");

  // Remove active from all desktop tabs
  desktopTabs.forEach(link => link.classList.remove("active"));
  const activeDesktopLink = document.querySelector(`.desktop-tabs a[data-tab="${tab}"]`);
  if (activeDesktopLink) activeDesktopLink.classList.add("active");

  localStorage.setItem("activeDashboardTab", tab);

  // Close sidebar after selecting a section on mobile
  if (window.innerWidth < 1024) {
    sidebar.classList.remove("open");
    hamburger.classList.remove("active");
  }
}


const savedTab = localStorage.getItem("activeDashboardTab") || tabs[0]?.dataset.tab;
if (savedTab) showSection(savedTab);

tabs.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    showSection(link.dataset.tab);
  });
});
desktopTabs.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    showSection(link.dataset.tab);
  });
});


  // -------------------------
  // LOG EVENTS FUNCTION
  // -------------------------
  async function logEvent(eventType, data = {}) {
    if (!window.user?.client_id) return;

    // Skip sending analytics for managers
    if (window.user.type !== "customer") return;

    const payload = {
      client_id: window.user.client_id,
      user_id: window.user.client_id,
      user_type: window.user.type,
      event_type: eventType,
      data: typeof data === "object" ? data : { value: data },
      timestamp: new Date().toISOString()
    };

    try {
      await fetch("/analytics/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      console.error(err);
    }
  }

  // -------------------------
  // CHATBOT LOGIC
  // -------------------------
  function addMessage(text, sender="bot") {
    if (!chatBox) return;
    const div = document.createElement("div");
    div.classList.add("chat-message", sender);
    const timeSpan = document.createElement("span");
    timeSpan.classList.add("timestamp");
    const now = new Date();
    timeSpan.textContent = now.getHours().toString().padStart(2,"0")+":"+now.getMinutes().toString().padStart(2,"0");
    div.textContent = text;
    div.appendChild(timeSpan);
    chatBox.appendChild(div);
    div.scrollIntoView({ behavior: "smooth", block: "end" });
  }

  async function typeBotMessage(text) {
    if (!chatBox) return;
    const div = document.createElement("div");
    div.classList.add("chat-message", "bot");
    chatBox.appendChild(div);
    for (let i = 0; i < text.length; i++) {
      div.textContent += text[i];
      chatBox.scrollTop = chatBox.scrollHeight;
      await new Promise(r => setTimeout(r, 30));
    }
  }

  function normalizeText(s) {
    return (s||"").toLowerCase().replace(/[\u2019']/g,"").replace(/[^a-z0-9\s]/g," ").replace(/\s+/g," ").trim();
  }
  function tokenize(s){return normalizeText(s).split(" ").filter(Boolean);}
  function jaccard(aTokens,bTokens){const A=new Set(aTokens);const B=new Set(bTokens);let inter=0;A.forEach(x=>{if(B.has(x)) inter++});const union=new Set([...A,...B]).size;return union?inter/union:0;}
  function findBestFaqMatch(question, faqData){
    if(!question||!faqData) return null;
    const qNorm=normalizeText(question),qTokens=tokenize(qNorm);
    let best={score:0,key:null};
    for(const key in faqData){
      const keyNorm=normalizeText(key);
      if(qNorm===keyNorm) return key;
      const keyTokens=tokenize(keyNorm);
      if(keyTokens.every(t=>qTokens.includes(t))) return key;
      const score=jaccard(qTokens,keyTokens);
      if(score>best.score) best={score,key};
    }
    return best.score>=0.35?best.key:null;
  }

  function sendQuestion(faqData=window.dbFaqs){
    if(!questionInput) return;
    const question=questionInput.value.trim();
    if(!question) return;
    addMessage(question,"user");
    logEvent("user_question",{question,user_id:window.user.client_id,source:"website"});
    let answer="❌ Sorry, I don’t know the answer to that.";
    const matchedKey=findBestFaqMatch(question,faqData);
    if(matchedKey){answer=faqData[matchedKey].answer;}
    typeBotMessage(answer);
    questionInput.value="";
  }

  askBtn?.addEventListener("click",()=>sendQuestion());
  questionInput?.addEventListener("keypress",e=>{if(e.key==="Enter")sendQuestion();});
  addMessage("👋 Hello! I'm Aether Smart FAQ Assistant. Ask me anything or pick a popular question below.");
  loadPopularQuestions();

  // -------------------------
  // FAQ MODULE
  // -------------------------
  async function loadFaqs() {
    try {
      if (!window.user?.client_id) throw new Error("No logged-in user");
      const res = await fetch(`/faqs/faq_data?client_id=${window.user.client_id}`);
      if (!res.ok) throw new Error("Failed to fetch FAQ data");
      const data = await res.json();
      window.dbFaqs = data.all || {};

      // Sidebar FAQ list
      if (faqQuestionsUL) {
        faqQuestionsUL.innerHTML = "";
        for (const question in window.dbFaqs) {
          const li = document.createElement("li");
          li.textContent = question;
          li.dataset.question = question;
          li.style.cursor = "pointer";
          faqQuestionsUL.appendChild(li);
        }
      }

      // Popular FAQs
      const popularList = document.getElementById("chatbot-faq-questions");
      if (popularList) {
        popularList.innerHTML = "";
        for (const question in window.dbFaqs) {
          if (window.dbFaqs[question].popular) {
            const li = document.createElement("li");
            li.className = "list-group-item list-group-item-action";
            li.textContent = question;
            li.addEventListener("click", () => {
              addMessage(question, "user");
              logEvent("faq_click", { question, user_id: window.user.client_id });
              const answer = window.dbFaqs[question]?.answer || "❌ Sorry, I don’t know the answer to that.";
              typeBotMessage(answer);
            });
            popularList.appendChild(li);
          }
        }
      }

      // CRUD FAQ list
      if (faqListDiv) {
        faqListDiv.innerHTML = "";
        for (const question in window.dbFaqs) {
          const faqItem = window.dbFaqs[question];
          if (!faqItem || !faqItem.answer) continue;

          const div = document.createElement("div");
          div.className = "faq-item";
          div.dataset.question = question;
          div.dataset.id = faqItem.id;

          div.innerHTML = `
            <strong>${question}</strong>: ${faqItem.answer} ${faqItem.popular ? "(Popular)" : ""}
            <button class="edit-btn">Edit</button>
            <button class="delete-btn">Delete</button>
          `;
          faqListDiv.appendChild(div);
        }
      }

      console.log("FAQs loaded. Count:", Object.keys(window.dbFaqs).length);
    } catch (err) {
      console.error("Error loading FAQs:", err);
    }
  }

  async function initFaqModule() {
    await loadFaqs();
    if (!faqListDiv) return;

    // CUSTOM CONFIRM MODAL
    function showConfirm(message, onConfirm) {
      const modal = document.getElementById("confirmModal");
      const msg = document.getElementById("confirmMessage");
      const yesBtn = document.getElementById("confirmYes");
      const noBtn = document.getElementById("confirmNo");
      if (!modal || !msg || !yesBtn || !noBtn) return;

      msg.textContent = message;
      modal.classList.remove("hidden");

      function cleanup() {
        modal.classList.add("hidden");
        yesBtn.removeEventListener("click", yesHandler);
        noBtn.removeEventListener("click", noHandler);
      }

      function yesHandler() { cleanup(); onConfirm?.(); }
      function noHandler() { cleanup(); }

      yesBtn.addEventListener("click", yesHandler);
      noBtn.addEventListener("click", noHandler);
    }

    // EDIT / DELETE HANDLER
    faqListDiv.addEventListener("click", async (e) => {
      const target = e.target;
      const faqDiv = target.closest(".faq-item");
      if (!faqDiv) return;

      const faqId = faqDiv.dataset.id;
      const question = faqDiv.dataset.question;
      const faqItem = window.dbFaqs[question];

// EDIT
if (target.classList.contains("edit-btn")) {
  faqQuestionInput.value = question;
  faqAnswerInput.value = faqItem.answer;

  // Update toggle state
  faqPopularCheckbox.checked = !!faqItem.popular; // ensure boolean
  popularLabel.textContent = faqPopularCheckbox.checked ? "Popular" : "Normal";

  // Scroll into view and store ID
  faqQuestionInput.dataset.id = faqItem.id;
  faqQuestionInput.scrollIntoView({ behavior: "smooth" });
}


      // DELETE
      if (target.classList.contains("delete-btn")) {
        showConfirm(`Are you sure you want to delete FAQ: "${question}"?`, async () => {
          try {
            const res = await fetch("/faqs/delete_faq", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ client_id: window.user.client_id, faq_id: faqId })
            });
            const data = await res.json();
            if (data.success) {
              await loadFaqs();
              showNotification("FAQ deleted successfully!", "success");
            } else {
              alert(data.error || "Failed to delete FAQ");
            }
          } catch (err) {
            console.error("Error deleting FAQ:", err);
            showNotification("Failed to delete FAQ!", "error");
          }
        });
      }
    });

    // Load analytics for this client
    loadAnalytics();
    setInterval(loadAnalytics, 30000); // Auto-refresh every 30s

    // ADD / UPDATE FAQ FORM
    addFaqForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const question = faqQuestionInput.value.trim();
      const answer = faqAnswerInput.value.trim();
      const popular = faqPopularCheckbox.checked ? 1 : 0;
      if (!question || !answer || !window.user?.client_id) return;

      try {
        const faqId = faqQuestionInput.dataset.id; // undefined if new
        const res = await fetch("/update_faq", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ client_id: window.user.client_id, faq_id: faqId, question, answer, popular })
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          alert(errData.error || "Failed to save FAQ");
          return;
        }

        const data = await res.json();
        if (data.success) {
          window.dbFaqs[question] = { id: data.id, answer, popular };
          await loadFaqs();
          faqQuestionInput.value = "";
          faqAnswerInput.value = "";
          faqPopularCheckbox.checked = false;
          popularLabel.textContent = "Normal";
          delete faqQuestionInput.dataset.id;
          showNotification("FAQ saved successfully!", "success");
        } else {
          alert(data.error || "Failed to save FAQ");
        }
      } catch (err) {
        console.error("Error saving FAQ:", err);
        showNotification("Failed to save FAQ!", "error");
      }
    });
  }

  initFaqModule();

// -------------------------
// SAVE WELCOME MESSAGE
// -------------------------
saveWelcomeBtn?.addEventListener("click", async () => {
  if (!window.user?.client_id) {
    console.error("❌ client_id missing!");
    showNotification("User not logged in!", "error");
    return;
  }

  const message = welcomeMessageTA.value.trim();
  if (!message) {
    showNotification("Welcome message cannot be empty!", "error");
    return;
  }

  console.log("Saving welcome message:", message, "for client_id:", window.user.client_id);

  try {
    const res = await fetch("/save_welcome_message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: window.user.client_id, message })
    });

    if (res.status === 404) {
      console.error("❌ Endpoint /save_welcome_message not found (404).");
      showNotification("Server route not found!", "error");
      return;
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      console.error("❌ Server response error:", errData);
      showNotification(errData.error || "Failed to save welcome message", "error");
      return;
    }

    const data = await res.json();
    if (data.success) {
      console.log("✅ Welcome message saved successfully.");
      showNotification("Welcome message saved successfully!", "success");
    } else {
      console.error("❌ Failed to save welcome message:", data.error);
      showNotification(data.error || "Failed to save welcome message", "error");
    }

  } catch (err) {
    console.error("❌ Network or server error:", err);
    showNotification("Network or server error! Could not save message.", "error");
  }
});



// -------------------------
// VIEW ALL FAQ BUTTON (TOGGLE)
// -------------------------
viewFaqsBtn?.addEventListener("click", () => {
  if (!faqListDiv) return;

  // Toggle hidden class
  faqListDiv.classList.toggle("hidden");

  // Scroll into view only when opening
  if (!faqListDiv.classList.contains("hidden")) {
    faqListDiv.scrollIntoView({ behavior: "smooth" });
  }
});


  // -------------------------
  // PREMIUM AI NOTIFICATION
  // -------------------------
  function showNotification(message, type = "info", duration = 4000) {
    const container = document.getElementById("notification-container");
    if (!container) return;

    const notif = document.createElement("div");
    notif.textContent = message;
    notif.style.padding = "14px 22px";
    notif.style.borderRadius = "12px";
    notif.style.color = "#fff";
    notif.style.fontSize = "14px";
    notif.style.fontWeight = "500";
    notif.style.fontFamily = "'Roboto', sans-serif";
    notif.style.boxShadow = "0 6px 18px rgba(0,0,0,0.3)";
    notif.style.backdropFilter = "blur(6px)";
    notif.style.opacity = "0";
    notif.style.transform = "translateY(-20px)";
    notif.style.transition = "opacity 0.35s ease, transform 0.35s ease";
    notif.style.pointerEvents = "auto";
    notif.style.cursor = "pointer";

    if (type === "success") notif.style.background = "linear-gradient(135deg, #00c6ff, #0072ff)";
    else if (type === "error") notif.style.background = "linear-gradient(135deg, #ff416c, #ff4b2b)";
    else notif.style.background = "linear-gradient(135deg, #8e2de2, #4a00e0)";

    container.appendChild(notif);

    requestAnimationFrame(() => {
      notif.style.opacity = "1";
      notif.style.transform = "translateY(0)";
    });

    notif.addEventListener("click", () => {
      notif.style.opacity = "0";
      notif.style.transform = "translateY(-20px)";
      setTimeout(() => notif.remove(), 350);
    });

    setTimeout(() => {
      notif.style.opacity = "0";
      notif.style.transform = "translateY(-20px)";
      setTimeout(() => notif.remove(), 350);
    }, duration);
  }

  // -------------------------
  // LOAD POPULAR QUESTIONS IN CHAT
  // -------------------------
  async function loadPopularQuestions() {
    try {
      if (!window.user?.client_id) return;
      const res = await fetch(`/faqs/faq_data?client_id=${window.user.client_id}`);
      if (!res.ok) throw new Error("Failed to fetch popular questions");

      const data = await res.json();
      const popularList = document.getElementById("chatbot-faq-questions");
      if (!popularList) return;
      popularList.innerHTML = "";

      const faqs = data.all || {};
      const popularFaqs = Object.keys(faqs).filter(q => faqs[q].popular);

      popularFaqs.forEach(q => {
        const li = document.createElement("li");
        li.className = "list-group-item list-group-item-action";
        li.style.cursor = "pointer";
        li.textContent = q;
        li.addEventListener("click", () => {
          addMessage(q, "user");
          logEvent("faq_click", { question: q, user_id: window.user.client_id });
          const answer = faqs[q]?.answer || "❌ Sorry, I don’t know the answer to that.";
          typeBotMessage(answer);
        });
        popularList.appendChild(li);
      });

    } catch (err) {
      console.error("Error loading popular questions:", err);
    }
  }

  // -------------------------
  // ANALYTICS
  // -------------------------
  async function loadAnalytics() {
    if (!window.user?.client_id) return;
    try {
      const res = await fetch(`/analytics/data?client_id=${window.user.client_id}`);
      if (!res.ok) throw new Error("Failed to fetch analytics data");
      const data = await res.json();

      if (totalInteractionsElem) totalInteractionsElem.textContent = data.total_interactions || 0;
      if (activeUsersElem) activeUsersElem.textContent = data.active_users || 0;

      if (faqUsageElem) {
        const faqUsed = data.faq_usage?.created || 0;
        const faqLimit = data.faq_usage?.limit || 50;
        faqUsageElem.textContent = `${faqUsed} / ${faqLimit} FAQs created`;

        const progressBar = document.getElementById("faq-progress-bar");
        if(progressBar) progressBar.style.width = `${Math.min((faqUsed / faqLimit) * 100, 100)}%`;
      }

      if (remainingAIRequestsElem) {
        const aiUsed = data.remaining_ai_requests?.used || 0;
        const aiLimit = data.remaining_ai_requests?.limit === Infinity ? "∞" : data.remaining_ai_requests?.limit;
        remainingAIRequestsElem.textContent = `${aiUsed} / ${aiLimit}`;
      }

    } catch (err) {
      console.error("❌ Error loading analytics:", err);
    }
  }

  

  if (window.user?.client_id) loadAnalytics();

});
