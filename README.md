# SMART INCIDENT TRIAGE AGENT FOR IT SUPPORT

Enterprise-looking, modular, fully runnable AI triage system for IT tickets:

- Severity classification (P1–P4)
- Team routing
- First-level troubleshooting suggestions
- Duplicate detection using semantic similarity
- Auto escalation for critical incidents (P1)
- Jira ticket creation (real if configured, mock otherwise)
- n8n workflow trigger (if configured)
- Analytics dashboard (Recharts) + Dark/Light mode

---

## Architecture (ASCII)

```
┌─────────────────────────────┐        ┌─────────────────────────────┐
│           Frontend          │        │           Backend           │
│   React + Vite + Tailwind   │  HTTP  │ FastAPI + SQLAlchemy + AI   │
│  Dashboard + Submit Ticket  ├────────►  /tickets /metrics /seed     │
└──────────────┬──────────────┘        └──────────────┬──────────────┘
               │                                      │
               │                                      │
               │                           ┌──────────▼──────────┐
               │                           │     AI Engine        │
               │                           │ OpenAI (if key)      │
               │                           │ Fallback rules       │
               │                           └──────────┬──────────┘
               │                                      │
               │                           ┌──────────▼──────────┐
               │                           │ Duplicate Detection   │
               │                           │ OpenAI embeddings OR  │
               │                           │ SentenceTransformers  │
               │                           └──────────┬──────────┘
               │                                      │
               │                           ┌──────────▼──────────┐
               │                           │ Escalation (P1)       │
               │                           │ Jira + n8n triggers    │
               │                           └──────────┬──────────┘
               │                                      │
               │                           ┌──────────▼──────────┐
               │                           │ SQLite (tickets)      │
               │                           └───────────────────────┘
```

---

## AI Decision Flow

1. **Rule-based override**
   - If description contains:
     - `production down`
     - `data breach`
     - `security incident`
     - `system outage`
   - Force `P1` and escalate.

2. **If OpenAI key exists**
   - OpenAI returns strict JSON:
     ```json
     { "severity": "P1|P2|P3|P4", "confidence": 0.0, "reasoning": "..." }
     ```
   - Team routing + fix suggestions are deterministic for consistency.

3. **If OpenAI key missing**
   - Fully deterministic severity classification + routing + fixes.

4. **Duplicate detection**
   - Embeddings via OpenAI (if configured) else SentenceTransformers
   - Cosine similarity (threshold 0.85)

5. **Escalation**
   - If `P1` => `escalated = true`
   - Create Jira issue (or mock)
   - Trigger n8n webhook (if configured)

---

## Run: Backend

From `smart-triage-agent/backend`:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`.

---

## Run: Frontend

From `smart-triage-agent/frontend`:

```bash
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

---

## Configure Jira (Optional)

Set in `.env` (copy from `.env.example`):

- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`

If any are missing, the backend returns a **mock Jira key** and does not crash.

---

## Configure n8n (Optional)

Set:

- `N8N_WEBHOOK_URL`

If missing, webhook trigger is skipped safely.

---

## Demo Walkthrough Script (Hackathon-ready)

1. Start backend + frontend.
2. Go to **Dashboard** → click **Seed Demo Data**.
3. Go to **Submit Ticket**:
   - Submit: “Production API returning 503… production down”
   - Observe:
     - Severity `P1`
     - Auto escalation banner
     - Jira key present (real or mock)
4. Submit a VPN ticket similar to seeded ticket:
   - Observe:
     - Duplicate detection (ticket id + similarity score)
5. Go back to **Dashboard**:
   - See charts update for severity and team routing

---

## Future Improvements

- Auth (SSO / OAuth2), role-based access control
- Real incident timeline + audit logs
- Async background jobs for Jira/n8n calls
- Vector DB for scalable dedupe (FAISS/pgvector)
- Fine-tuned severity classifier with historical tickets
- Alerting integrations (Slack/Teams/PagerDuty)
