// server.js
const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Open SQLite database
const db = new sqlite3.Database("db.sqlite", (err) => {
  if (err) console.error("Failed to connect to DB:", err);
  else console.log("Connected to SQLite database");
});

// -------------------------
// Helper: Get client plan limits
// -------------------------
function getClientLimits(plan) {
  const plans = {
    demo: 100,
    onetime: 500,
    basic: 1000,
    standard: 5000,
    premium: Infinity,
  };
  return plans[plan] || 100;
}

// -------------------------
// ANALYTICS ROUTE
// -------------------------
app.get("/analytics/data", (req, res) => {
  const client_id = req.query.client_id;
  if (!client_id) return res.status(400).json({ error: "Missing client_id" });

  // 1️⃣ Total interactions
  const totalQuery = `
    SELECT COUNT(*) AS total_interactions 
    FROM interaction_logs 
    WHERE client_id = ? AND role='user' AND source='customer'`;

  // 2️⃣ Active users (distinct user_id)
  const activeUsersQuery = `
    SELECT COUNT(DISTINCT user_id) AS active_users
    FROM interaction_logs
    WHERE client_id = ? AND role='user' AND source='customer'`;

  // 3️⃣ FAQ usage
  const faqQuery = `
    SELECT COUNT(*) AS faq_usage 
    FROM interaction_logs 
    WHERE client_id = ? AND event_type='faq_click' AND role='user' AND source='customer'`;

  // 4️⃣ AI usage
  const aiQuery = `
    SELECT COUNT(*) AS ai_usage 
    FROM interaction_logs 
    WHERE client_id = ? AND event_type='ai_request' AND role='user' AND source='customer'`;

  // 5️⃣ Daily counts for last 30 days
  const dailyQuery = `
    SELECT DATE(created_at) AS day,
           SUM(CASE WHEN event_type='faq_click' THEN 1 ELSE 0 END) AS faq_count,
           SUM(CASE WHEN event_type='ai_request' THEN 1 ELSE 0 END) AS ai_count
    FROM interaction_logs
    WHERE client_id = ? AND role='user' AND source='customer' 
          AND DATE(created_at) >= DATE('now','-30 days')
    GROUP BY day
    ORDER BY day`;

  db.get(totalQuery, [client_id], (err1, totalRow) => {
    if (err1) return res.status(500).json({ error: err1.message });

    db.get(activeUsersQuery, [client_id], (err2, activeRow) => {
      if (err2) return res.status(500).json({ error: err2.message });

      db.get(faqQuery, [client_id], (err3, faqRow) => {
        if (err3) return res.status(500).json({ error: err3.message });

        db.get(aiQuery, [client_id], (err4, aiRow) => {
          if (err4) return res.status(500).json({ error: err4.message });

          db.all(dailyQuery, [client_id], (err5, dailyRows) => {
            if (err5) return res.status(500).json({ error: err5.message });

            const daily = {
              labels: dailyRows.map(r => r.day),
              faq_counts: dailyRows.map(r => r.faq_count),
              ai_counts: dailyRows.map(r => r.ai_count),
            };

            // Example: get client plan (hardcoded for demo)
            const plan = "demo"; // replace with DB lookup if needed
            const limit = getClientLimits(plan);

            res.json({
              total_interactions: totalRow.total_interactions || 0,
              active_users: activeRow.active_users || 0,
              faq_usage: { used: faqRow.faq_usage || 0, limit },
              remaining_ai_requests: { used: aiRow.ai_usage || 0, limit },
              new_leads: 0, // add logic if you track leads
              daily,
            });
          });
        });
      });
    });
  });
});

// -------------------------
// LOG INTERACTION ROUTE
// -------------------------
app.post("/analytics/log", (req, res) => {
  const { client_id, event_type, data, timestamp } = req.body;
  if (!client_id || !event_type) return res.status(400).json({ error: "Missing required fields" });

  const user_id = data?.user_id || "anonymous";
  const source = data?.source || "customer"; // default to customer
  const role = "user"; // always role=user for customer interactions

  db.run(
    `INSERT INTO interaction_logs (client_id, user_id, role, source, event_type, created_at)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [client_id, user_id, role, source, event_type, timestamp || new Date().toISOString()],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// -------------------------
// START SERVER
// -------------------------
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
