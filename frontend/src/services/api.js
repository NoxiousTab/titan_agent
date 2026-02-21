import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 30000
});

export async function createTicket(payload) {
  const res = await api.post("/tickets", payload);
  return res.data;
}

export async function listTickets() {
  const res = await api.get("/tickets");
  return res.data;
}

export async function getMetrics() {
  const res = await api.get("/dashboard/metrics");
  return res.data;
}

export async function seedDemo() {
  const res = await api.post("/seed");
  return res.data;
}

export async function simulateDatadogAlert() {
  const payload = {
    title: "High CPU usage on prod-server-01",
    text: "CPU usage above 95% for 5 minutes",
    alert_type: "error",
    priority: "P1",
    host: "prod-server-01",
    monitor_name: "CPU Threshold Monitor",
    monitor_id: 12345,
    event_type: "triggered"
  };
  const res = await api.post("/monitoring/datadog", payload);
  return res.data;
}
