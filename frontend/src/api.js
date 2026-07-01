import axios from "axios";

export const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "") || "http://localhost:8000";

function headers() {
  const apiKey = localStorage.getItem("al_apikey") || "";
  const token = localStorage.getItem("al_token") || "";
  return {
    ...(apiKey ? { "x-api-key": apiKey } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

const api = axios.create({ baseURL: BASE });
api.interceptors.request.use(cfg => { cfg.headers = { ...cfg.headers, ...headers() }; return cfg; });
api.interceptors.response.use(r => r.data, e => Promise.reject(e?.response?.data || e));

export const getDashboard = (days = 7) => api.get(`/dashboard?days=${days}`);
export const getConversations = (params = {}) => api.get("/conversations", { params });
export const getSessions = (limit = 20) => api.get(`/sessions?limit=${limit}`);
export const getSession = (id) => api.get(`/sessions/${id}`);
export const triggerAnalysis = (limit = 100) => api.post("/analyze", { limit });
export const suggestPrompt = (current_prompt) => api.post("/suggest-prompt", { current_prompt });
export const getProjects = () => api.get("/projects");
export const createProject = (name) => api.post("/projects", { name });
export const getAlertConfig = () => api.get("/alerts/config");
export const updateAlertConfig = (cfg) => api.put("/alerts/config", cfg);
export const testAlert = () => api.post("/test-alert");
export const exportCsvUrl = (failuresOnly = false) =>
  `${BASE}/export?failures_only=${failuresOnly}&x-api-key=${encodeURIComponent(localStorage.getItem("al_apikey") || "")}`;
export const signup = (email, password) => api.post("/auth/signup", { email, password });
export const loginApi = (email, password) => api.post("/auth/login", { email, password });
export const WS_URL = BASE.replace(/^http/, "ws") + "/ws/";
