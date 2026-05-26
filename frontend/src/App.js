import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import Conversations from "./pages/Conversations";
import PromptLab from "./pages/PromptLab";
import {
  LayoutDashboard, MessageSquare, Wand2, Activity
} from "lucide-react";
import "./index.css";

const qc = new QueryClient();

function Sidebar() {
  const links = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/conversations", icon: MessageSquare, label: "Conversations" },
    { to: "/prompt-lab", icon: Wand2, label: "Prompt Lab" },
  ];
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
      </BrowserRouter>
    </QueryClientProvider>
  );
}
