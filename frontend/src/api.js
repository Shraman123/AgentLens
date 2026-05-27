import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const getApiKey = () => localStorage.getItem("api_key") || process.env.REACT_APP_API_KEY || "ak_demo_123456789";
const getToken = () => localStorage.getItem("token");

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use(config => {
  const apiKey = getApiKey();
  const token = getToken();
  if (apiKey) config.headers["x-api-key"] = apiKey;
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});

export const getDashboard = () => api.get("/dashboard").then(r => r.data);
export const getConversations = (params) => api.get("/conversations", { params }).then(r => r.data);
export const triggerAnalysis = (limit = 50) => api.post("/analyze", { limit }).then(r => r.data);
export const suggestPrompt = (current_prompt) => api.post("/suggest-prompt", { current_prompt }).then(r => r.data);
export const getProjects = () => api.get("/projects").then(r => r.data);
export const createProject = (name) => api.post("/projects", { name }).then(r => r.data);

export default api;
