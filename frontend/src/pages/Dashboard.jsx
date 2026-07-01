import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { Zap, RefreshCw, Wifi, WifiOff, Download } from "lucide-react";
import { getDashboard, triggerAnalysis, exportCsvUrl, WS_URL } from "../api.js";
import { useAuth } from "../App.jsx";

const SENT_COLORS = { positive: "#00ff88", neutral: "#444", negative: "#ff4444" };

function StatCard({ label, value, sub, color = "accent" }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${color}`}>{value ?? "—"}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function Skeleton({ h = 20, w = "100%" }) {
  return <div className="skeleton" style={{ height: h, width: w }} />;
}

export default function Dashboard() {
  const qc = useQueryClient();
  const { apiKey } = useAuth();
  const [days, setDays] = useState(7);
  const [toast, setToast] = useState(null);
  const [wsStatus, setWsStatus] = useState("connecting");
  const wsRef = useRef(null);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", days],
    queryFn: () => getDashboard(days),
    refetchInterval: 30_000,
  });

  const analyze = useMutation({
    mutationFn: () => triggerAnalysis(100),
    onSuccess: (res) => {
      qc.invalidateQueries(["dashboard"]);
      showToast(`Analyzed ${res.analyzed} conversations`, "success");
    },
    onError: () => showToast("Analysis failed", "error"),
  });

  function showToast(msg, type) {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  }

  // WebSocket for real-time events
  useEffect(() => {
    if (!apiKey) return;
    const url = WS_URL + encodeURIComponent(apiKey);
    function connect() {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => { setWsStatus("disconnected"); setTimeout(connect, 5000); };
      ws.onerror = () => setWsStatus("disconnected");
      ws.onmessage = (e) => {
        try {
          const ev = JSON.parse(e.data);
          if (ev.type === "new_conversation") {
            qc.invalidateQueries(["dashboard"]);
          }
          if (ev.type === "analysis_complete") {
            qc.invalidateQueries(["dashboard"]);
            showToast(`Auto-analysis: ${ev.analyzed} processed`, "success");
          }
        } catch {}
      };
    }
    connect();
    return () => { wsRef.current?.close(); };
  }, [apiKey, qc]);

  const d = data || {};
  const stats = d.stats || {};
  const intents = d.top_intents || [];
  const sentiments = d.sentiments || [];
  const daily = [...(d.daily_volume || [])];
  const maxIntent = intents[0]?.count || 1;
  const pieData = sentiments.map(s => ({ name: s.sentiment, value: s.count, color: SENT_COLORS[s.sentiment] || "#888" }));

  return (
    <div>
      {toast && <div className={`toast ${toast.type}`}>{toast.msg}</div>}

      <div className="page-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="page-title">{d.project?.name || "Dashboard"}</div>
            <div className="page-sub">
              Real-time intelligence on your AI agent
              <span className={`ws-badge ${wsStatus}`}>
                {wsStatus === "connected" ? <><Wifi size={10} /> Live</> : <><WifiOff size={10} /> Reconnecting…</>}
              </span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div className="days-select">
              {[7, 14, 30].map(d => (
                <button key={d} className={`days-btn ${days === d ? "active" : ""}`} onClick={() => setDays(d)}>{d}d</button>
              ))}
            </div>
            <a href={exportCsvUrl()} download className="btn btn-ghost">
              <Download size={13} /> Export
            </a>
            <button className="btn btn-primary" onClick={() => analyze.mutate()} disabled={analyze.isPending}>
              {analyze.isPending
                ? <><span className="spinner" style={{ margin: 0, width: 12, height: 12, borderWidth: 2 }} /> Analyzing…</>
                : <><Zap size={14} /> Run Analysis</>}
            </button>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        {isLoading
          ? Array(5).fill(0).map((_, i) => <div key={i} className="stat-card"><Skeleton h={48} /></div>)
          : <>
            <StatCard label="Total Conversations" value={stats.total ?? 0} color="accent" />
            <StatCard label="Analyzed" value={stats.analyzed ?? 0} color="blue" sub={`${stats.total ? Math.round((stats.analyzed / stats.total) * 100) : 0}% coverage`} />
            <StatCard label="Failures" value={stats.failures ?? 0} color="red" />
            <StatCard label="Failure Rate" value={`${stats.failure_rate ?? 0}%`} color={stats.failure_rate > 20 ? "red" : "yellow"} />
            <StatCard label="Avg Latency" value={stats.avg_latency_ms ? `${stats.avg_latency_ms}ms` : "—"} color="accent" />
          </>}
      </div>

      <div className="panels-row">
        <div className="panel">
          <div className="panel-title">Top Intents</div>
          {isLoading
            ? Array(5).fill(0).map((_, i) => <Skeleton key={i} h={28} w="100%" />)
            : intents.length === 0
              ? <div className="empty-state">No intents yet — run analysis first</div>
              : intents.map((item) => (
                <div className="intent-row" key={item.intent}>
                  <div className="intent-label">{item.intent}</div>
                  <div className="intent-bar-wrap">
                    <div className="intent-bar-fill" style={{ width: `${(item.count / maxIntent) * 100}%` }} />
                  </div>
                  <div className="intent-count">{item.count}</div>
                </div>
              ))}
        </div>

        <div className="panel">
          <div className="panel-title">Sentiment Distribution</div>
          {isLoading
            ? <Skeleton h={160} />
            : pieData.length === 0
              ? <div className="empty-state">No sentiment data yet</div>
              : <>
                <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                  {pieData.map(p => (
                    <div key={p.name} className={`sentiment-pill ${p.name}`}>{p.name} · {p.value}</div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={140}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#111", border: "1px solid #222", borderRadius: 6, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </>}
        </div>
      </div>

      <div className="panel-full">
        <div className="panel-title">Conversation Volume — Last {days} Days</div>
        {isLoading
          ? <Skeleton h={160} />
          : daily.length === 0
            ? <div className="empty-state">No data yet</div>
            : <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={daily} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fill: "#555", fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                <YAxis tick={{ fill: "#555", fontSize: 11, fontFamily: "IBM Plex Mono" }} />
                <Tooltip contentStyle={{ background: "#111", border: "1px solid #222", borderRadius: 6, fontSize: 12 }} />
                <Area type="monotone" dataKey="count" stroke="#00ff88" strokeWidth={2} fill="url(#volGrad)" />
              </AreaChart>
            </ResponsiveContainer>}
      </div>

      <div className="panel-full">
        <div className="panel-title">Recent Conversations</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>User Message</th>
                <th>Agent Response</th>
                <th>Intent</th>
                <th>Sentiment</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array(5).fill(0).map((_, i) => (
                  <tr key={i}>{Array(6).fill(0).map((_, j) => <td key={j}><Skeleton h={14} /></td>)}</tr>
                ))
                : (d.recent_conversations || []).map(c => (
                  <tr key={c.id}>
                    <td className="msg-cell" title={c.user_message}>{c.user_message}</td>
                    <td className="msg-cell" title={c.agent_response}>{c.agent_response}</td>
                    <td>{c.intent ? <span className="badge badge-intent">{c.intent}</span> : <span className="dim">—</span>}</td>
                    <td>{c.sentiment ? <span className={`badge badge-${c.sentiment}`}>{c.sentiment}</span> : "—"}</td>
                    <td>{c.is_failure ? <span className="badge badge-failure">failure</span> : <span className="ok-text">✓ ok</span>}</td>
                    <td className="time-cell">{c.created_at ? new Date(c.created_at).toLocaleTimeString() : "—"}</td>
                  </tr>
                ))}
              {!isLoading && !d.recent_conversations?.length && (
                <tr><td colSpan={6} className="empty-state">No conversations logged yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
