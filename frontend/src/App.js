import React from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import Conversations from "./pages/Conversations";
import PromptLab from "./pages/PromptLab";
import Login from "./pages/Login";
import { LayoutDashboard, MessageSquare, Wand2, Activity, LogOut, Key } from "lucide-react";
import "./index.css";

const qc = new QueryClient();

function PrivateRoute({ children }) {
  const token = localStorage.getItem("token");
  const apiKey = localStorage.getItem("api_key");
  // allow access if logged in OR using demo api key
  if (!token && !apiKey) return <Navigate to="/login" />;
  return children;
}

function Sidebar() {
  const navigate = useNavigate();
  const project = JSON.parse(localStorage.getItem("project") || "{}");
  const apiKey = localStorage.getItem("api_key") || "ak_demo_123456789";

  const links = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/conversations", icon: MessageSquare, label: "Conversations" },
    { to: "/prompt-lab", icon: Wand2, label: "Prompt Lab" },
  ];

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  return (
    <aside className="sidebar">
      <div className="logo">
        <Activity size={20} />
        <span>AgentLens</span>
      </div>
      <nav>
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) =>
            `nav-link ${isActive ? "active" : ""}`
          }>
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: "12px 8px", borderTop: "1px solid var(--border)" }}>
        <div style={{ padding: "8px 12px", marginBottom: 4 }}>
          <div style={{ fontSize: 10, color: "var(--text3)", fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
            <Key size={10} style={{ display: "inline", marginRight: 4 }} />API Key
          </div>
          <div style={{ fontSize: 10, color: "var(--text3)", fontFamily: "IBM Plex Mono", wordBreak: "break-all" }}>
            {apiKey?.slice(0, 16)}...
          </div>
        </div>
        {localStorage.getItem("token") && (
          <button onClick={handleLogout} className="nav-link" style={{ width: "100%", background: "none", border: "none", cursor: "pointer", color: "var(--text3)" }}>
            <LogOut size={16} /> Sign out
          </button>
        )}
      </div>
      <div className="sidebar-footer">
        <span className="badge-live">● LIVE</span>
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <PrivateRoute>
              <div className="app-shell">
                <Sidebar />
                <main className="main-content">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/conversations" element={<Conversations />} />
                    <Route path="/prompt-lab" element={<PromptLab />} />
                  </Routes>
                </main>
              </div>
            </PrivateRoute>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
