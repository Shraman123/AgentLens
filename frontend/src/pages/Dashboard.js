import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { getDashboard, triggerAnalysis } from "../api";
import { Zap, RefreshCw } from "lucide-react";

function Toast({ msg, type, onClose }) {
  React.useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [onClose]);
  return <div className={`toast ${type}`}>{msg}</div>;
}

export default function Dashboard() {
  const qc = useQueryClient();
  const [toast, setToast] = useState(null);
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard, refetchInterval: 10000 });
  const analyze = useMutation({
    mutationFn: () => triggerAnalysis(100),
    onSuccess: (res) => {
      qc.invalidateQueries(["dashboard"]);
      setToast({ msg: `✓ Analyzed ${res.analyzed} conversations`, type: "success" });
    },
    onError: () => setToast({ msg: "Analysis failed. Check API key + server.", type: "error" })
  });

  if (isLoading) return <div className="loading"><div className="spinner" />Loading...</div>;

  const d = data || {};
  const stats = d.stats || {};
  const intents = d.top_intents || [];
  const sentiments = d.sentiments || [];
  const daily = [...(d.daily_volume || [])].reverse();
  const maxIntent = intents[0]?.count || 1;

  const sentMap = { positive: 0, neutral: 0, negative: 0 };
  sentiments.forEach(s => { sentMap[s.sentiment] = s.count; });
  const total = Object.values(sentMap).reduce((a, b) => a + b, 0) || 1;

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
      <div className="page-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="page-title">{d.project?.name || "Dashboard"}</div>
            <div className="page-sub">Real-time intelligence on your AI agent</div>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => analyze.mutate()}
            disabled={analyze.isPending}
          >
            {analyze.isPending
              ? <><div className="spinner" style={{ margin: 0, width: 12, height: 12, borderWidth: 2 }} /> Analyzing...</>
              : <><Zap size={14} /> Run Analysis</>
            }
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Conversations</div>
          <div className="stat-value accent">{stats.total ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Analyzed</div>
          <div className="stat-value blue">{stats.analyzed ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Failures</div>
          <div className="stat-value red">{stats.failures ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Failure Rate</div>
          <div className="stat-value yellow">{stats.failure_rate ?? 0}%</div>
        </div>
      </div>

      <div className="panels-row">
        <div className="panel">
          <div className="panel-title">Top Intents</div>
          {intents.length === 0
            ? <div className="empty-state">No intents yet — run analysis first</div>
            : intents.map((item) => (
              <div className="intent-row" key={item.intent}>
                <div className="intent-label">{item.intent}</div>
                <div className="intent-bar-wrap">
                  <div className="intent-bar-fill" style={{ width: `${(item.count / maxIntent) * 100}%` }} />
                </div>
                <div className="intent-count">{item.count}</div>
              </div>
            ))
          }
        </div>

        <div className="panel">
          <div className="panel-title">Sentiment Breakdown</div>
          {total === 1
            ? <div className="empty-state">No sentiment data yet</div>
            : <>
              <div className="sentiment-row" style={{ marginBottom: 20 }}>
                {["positive", "neutral", "negative"].map(s => (
                  <div key={s} className={`sentiment-pill ${s}`}>
                    {s} · {Math.round(sentMap[s] / total * 100)}%
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={[{ positive: sentMap.positive, neutral: sentMap.neutral, negative: sentMap.negative }]}>
                  <Tooltip contentStyle={{ background: "#111", border: "1px solid #222", borderRadius: 6, fontSize: 12 }} />
                  <Bar dataKey="positive" fill="#00ff88" radius={[3,3,0,0]} />
                  <Bar dataKey="neutral" fill="#333" radius={[3,3,0,0]} />
                  <Bar dataKey="negative" fill="#ff4444" radius={[3,3,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          }
        </div>
      </div>

      <div className="panel-full">
        <div className="panel-title">Daily Volume (Last 7 Days)</div>
        {daily.length === 0
          ? <div className="empty-state">No data yet</div>
          : <ResponsiveContainer width="100%" height={160}>
            <BarChart data={daily} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="day" tick={{ fill: "#555", fontSize: 11, fontFamily: "IBM Plex Mono" }} />
              <YAxis tick={{ fill: "#555", fontSize: 11, fontFamily: "IBM Plex Mono" }} />
              <Tooltip contentStyle={{ background: "#111", border: "1px solid #222", borderRadius: 6, fontSize: 12 }} />
              <Bar dataKey="count" fill="#00ff88" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        }
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
              {(d.recent_conversations || []).map(c => (
                <tr key={c.id}>
                  <td className="msg-cell" title={c.user_message}>{c.user_message}</td>
                  <td className="msg-cell" title={c.agent_response}>{c.agent_response}</td>
                  <td>{c.intent ? <span className="badge badge-intent">{c.intent}</span> : <span style={{ color: "var(--text3)" }}>—</span>}</td>
                  <td>{c.sentiment ? <span className={`badge badge-${c.sentiment}`}>{c.sentiment}</span> : "—"}</td>
                  <td>{c.is_failure ? <span className="badge badge-failure">failure</span> : <span style={{ color: "var(--accent)", fontSize: 11 }}>✓ ok</span>}</td>
                  <td style={{ color: "var(--text3)", fontFamily: "IBM Plex Mono", fontSize: 11 }}>
                    {c.created_at ? new Date(c.created_at).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              ))}
              {!d.recent_conversations?.length && (
                <tr><td colSpan={6} className="empty-state">No conversations logged yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
