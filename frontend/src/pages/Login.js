import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Activity } from "lucide-react";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("login"); // login | signup
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong");

      if (mode === "login") {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));
      } else {
        // signup — store api key and redirect
        localStorage.setItem("api_key", data.project.api_key);
        localStorage.setItem("project", JSON.stringify(data.project));
      }

      // fetch projects to get api key
      if (mode === "login") {
        const projRes = await fetch(`${API}/projects`, {
          headers: { "Authorization": `Bearer ${data.access_token}` }
        });
        const projects = await projRes.json();
        if (projects.length > 0) {
          localStorage.setItem("api_key", projects[0].api_key);
          localStorage.setItem("project", JSON.stringify(projects[0]));
        }
      }

      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", background: "#080808", display: "flex",
      alignItems: "center", justifyContent: "center", padding: "24px"
    }}>
      <div style={{ width: "100%", maxWidth: 400 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontFamily: "IBM Plex Mono", fontWeight: 700, fontSize: 18,
            color: "#00ff88", marginBottom: 8
          }}>
            <Activity size={20} /> AgentLens
          </div>
          <div style={{ color: "#555", fontSize: 13, fontFamily: "IBM Plex Mono" }}>
            {mode === "login" ? "Sign in to your account" : "Create your free account"}
          </div>
        </div>

        <div style={{
          background: "#0f0f0f", border: "1px solid #1e1e1e",
          borderRadius: 8, padding: 32
        }}>
          {error && (
            <div style={{
              background: "rgba(255,68,68,0.08)", border: "1px solid rgba(255,68,68,0.2)",
              borderRadius: 6, padding: "10px 14px", marginBottom: 20,
              color: "#ff4444", fontSize: 13, fontFamily: "IBM Plex Mono"
            }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 11, color: "#555", fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@company.com"
              style={{
                width: "100%", background: "#161616", border: "1px solid #2a2a2a",
                borderRadius: 6, padding: "10px 14px", color: "#f0f0f0",
                fontFamily: "IBM Plex Mono", fontSize: 13, outline: "none",
                boxSizing: "border-box"
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 11, color: "#555", fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%", background: "#161616", border: "1px solid #2a2a2a",
                borderRadius: 6, padding: "10px 14px", color: "#f0f0f0",
                fontFamily: "IBM Plex Mono", fontSize: 13, outline: "none",
                boxSizing: "border-box"
              }}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{
              width: "100%", background: "#00ff88", color: "#000",
              border: "none", borderRadius: 6, padding: "12px",
              fontFamily: "IBM Plex Mono", fontWeight: 700, fontSize: 14,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>

          <div style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "#555" }}>
            {mode === "login" ? (
              <>Don't have an account?{" "}
                <span onClick={() => setMode("signup")} style={{ color: "#00ff88", cursor: "pointer" }}>Sign up free</span>
              </>
            ) : (
              <>Already have an account?{" "}
                <span onClick={() => setMode("login")} style={{ color: "#00ff88", cursor: "pointer" }}>Sign in</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
