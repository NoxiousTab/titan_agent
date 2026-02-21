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
