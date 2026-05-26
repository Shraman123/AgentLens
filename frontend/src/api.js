import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const API_KEY = process.env.REACT_APP_API_KEY || "ak_demo_123456789";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "x-api-key": API_KEY },
});

export const getDashboard = () => api.get("/dashboard").then((r) => r.data);
export const getConversations = (params) =>
  api.get("/conversations", { params }).then((r) => r.data);
export const triggerAnalysis = (limit = 50) =>
  api.post("/analyze", { limit }).then((r) => r.data);
export const suggestPrompt = (current_prompt) =>
  api.post("/suggest-prompt", { current_prompt }).then((r) => r.data);

export default api;
