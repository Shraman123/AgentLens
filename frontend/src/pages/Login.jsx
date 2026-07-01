import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signup, loginApi } from "../api.js";
import { useAuth } from "../App.jsx";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [tab, setTab] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const data = tab === "signup" ? await signup(email, password) : await loginApi(email, password);
      login(data);
      nav("/dashboard");
    } catch (err) {
      setError(err?.detail || err?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">⚡ AgentLens</div>
        <div className="login-tagline">Monitor your AI agents in production</div>

        <div className="login-tabs">
          <button className={`login-tab ${tab === "login" ? "active" : ""}`} onClick={() => setTab("login")}>Sign in</button>
          <button className={`login-tab ${tab === "signup" ? "active" : ""}`} onClick={() => setTab("signup")}>Create account</button>
        </div>

        <form onSubmit={submit} className="login-form">
          <div className="field">
            <label className="field-label">Email</label>
            <input className="field-input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label className="field-label">Password</label>
            <input className="field-input" type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
          </div>
          {error && <div className="login-error">{error}</div>}
          <button className="btn btn-primary btn-full" disabled={loading}>
            {loading ? <span className="spinner" style={{ margin: 0, width: 14, height: 14, borderWidth: 2 }} /> : null}
            {tab === "signup" ? "Create account" : "Sign in"}
          </button>
        </form>

        <div className="login-demo">
          <div className="login-demo-title">What you get</div>
          <div className="login-demo-items">
            <span>⚡ Real-time conversation feed</span>
            <span>🔍 AI-powered failure detection</span>
            <span>🧠 Automatic prompt improvements</span>
            <span>📧 Email alerts on failure spikes</span>
          </div>
        </div>
      </div>
    </div>
  );
}
