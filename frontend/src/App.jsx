import React, { createContext, useContext, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import {
  LayoutDashboard, MessageSquare, Wand2, Bell, LogOut,
  Key, ChevronRight, Layers,
} from "lucide-react";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Conversations from "./pages/Conversations.jsx";
import PromptLab from "./pages/PromptLab.jsx";
import Sessions from "./pages/Sessions.jsx";
import AlertsConfig from "./pages/AlertsConfig.jsx";

export const AuthCtx = createContext(null);
export function useAuth() { return useContext(AuthCtx); }

function getStored(key) {
  try { return localStorage.getItem(key) || ""; } catch { return ""; }
}

export default function App() {
  const [token, setToken] = useState(getStored("al_token"));
  const [apiKey, setApiKey] = useState(getStored("al_apikey"));
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem("al_user") || "null"); } catch { return null; } });

  function login(data) {
    setToken(data.access_token || "");
    setApiKey(data.project?.api_key || data.api_key || "");
    setUser(data.user || null);
    localStorage.setItem("al_token", data.access_token || "");
    localStorage.setItem("al_apikey", data.project?.api_key || data.api_key || "");
    localStorage.setItem("al_user", JSON.stringify(data.user || null));
  }

  function logout() {
    setToken(""); setApiKey(""); setUser(null);
    ["al_token", "al_apikey", "al_user"].forEach(k => localStorage.removeItem(k));
  }

  const isAuthed = Boolean(apiKey);

  return (
    <AuthCtx.Provider value={{ token, apiKey, user, login, logout, isAuthed }}>
      <BrowserRouter>
        {isAuthed ? <AppShell onLogout={logout} /> : <LoginShell />}
      </BrowserRouter>
    </AuthCtx.Provider>
  );
}

function LoginShell() {
  return (
    <Routes>
      <Route path="*" element={<Login />} />
    </Routes>
  );
}

const NAV = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/conversations", icon: MessageSquare, label: "Conversations" },
  { to: "/sessions", icon: Layers, label: "Sessions" },
  { to: "/prompt-lab", icon: Wand2, label: "Prompt Lab" },
  { to: "/alerts", icon: Bell, label: "Alerts" },
];

function AppShell({ onLogout }) {
  const { apiKey, user } = useAuth();

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">AgentLens</span>
        </div>

        <div className="sidebar-nav">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
              <Icon size={15} />
              <span>{label}</span>
              <ChevronRight size={12} className="nav-arrow" />
            </NavLink>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="api-key-box">
            <div className="api-key-label"><Key size={10} /> API Key</div>
            <div className="api-key-val">{apiKey?.slice(0, 16)}…</div>
          </div>
          {user && <div className="user-email">{user.email}</div>}
          <button className="btn-logout" onClick={onLogout}>
            <LogOut size={13} /> Sign out
          </button>
        </div>
      </nav>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/conversations" element={<Conversations />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/prompt-lab" element={<PromptLab />} />
          <Route path="/alerts" element={<AlertsConfig />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}
