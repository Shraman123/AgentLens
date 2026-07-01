import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { X, MessageSquare, AlertTriangle, Clock } from "lucide-react";
import { getSessions, getSession } from "../api.js";

function SessionReplay({ sessionId, onClose }) {
  const { data, isLoading } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
    enabled: Boolean(sessionId),
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Session Replay</div>
            <div className="modal-sub">{sessionId}</div>
          </div>
          <button className="modal-close" onClick={onClose}><X size={14} /></button>
        </div>
        <div className="modal-body replay-body">
          {isLoading
            ? <div className="loading"><div className="spinner" />Loading session…</div>
            : (data?.turns || []).map((turn, i) => {
              let meta = {}; try { meta = JSON.parse(turn.metadata || "{}"); } catch {}
              return (
                <div key={turn.id} className="replay-turn">
                  <div className="replay-turn-header">
                    <span className="replay-turn-n">Turn {i + 1}</span>
                    {turn.is_failure && <span className="badge badge-failure">failure</span>}
                    {turn.intent && <span className="badge badge-intent">{turn.intent}</span>}
                    {turn.sentiment && <span className={`badge badge-${turn.sentiment}`}>{turn.sentiment}</span>}
                    {meta.latency_ms && <span className="meta-chip"><Clock size={9} /> {meta.latency_ms}ms</span>}
                  </div>
                  <div className="conv-block user">
                    <div className="conv-block-label">User</div>
                    <div className="conv-block-text">{turn.user_message}</div>
                  </div>
                  <div className="conv-block agent">
                    <div className="conv-block-label">Agent</div>
                    <div className="conv-block-text">{turn.agent_response}</div>
                  </div>
                  {turn.failure_reason && (
                    <div className="conv-failure-reason"><AlertTriangle size={11} /> {turn.failure_reason}</div>
                  )}
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}

export default function Sessions() {
  const [selected, setSelected] = useState(null);
  const { data, isLoading } = useQuery({ queryKey: ["sessions"], queryFn: () => getSessions(50) });
  const sessions = data?.sessions || [];

  return (
    <div>
      {selected && <SessionReplay sessionId={selected} onClose={() => setSelected(null)} />}
      <div className="page-header">
        <div className="page-title">Sessions</div>
        <div className="page-sub">Group conversations by user session — click to replay</div>
      </div>

      <div className="sessions-grid">
        {isLoading
          ? Array(8).fill(0).map((_, i) => <div key={i} className="session-card skeleton-card"><div className="skeleton" style={{ height: 80 }} /></div>)
          : sessions.length === 0
            ? <div className="empty-state" style={{ gridColumn: "1/-1" }}>No sessions yet. Log conversations with a session_id to see them here.</div>
            : sessions.map(s => (
              <div key={s.session_id} className="session-card clickable-row" onClick={() => setSelected(s.session_id)}>
                <div className="session-id">{s.session_id?.slice(0, 20)}…</div>
                <div className="session-preview">{s.first_message?.slice(0, 80)}</div>
                <div className="session-meta">
                  <span><MessageSquare size={11} /> {s.turns} turns</span>
                  {s.failures > 0 && <span className="session-failures"><AlertTriangle size={11} /> {s.failures} failures</span>}
                  <span className="dim">{s.last_active ? new Date(s.last_active).toLocaleDateString() : "—"}</span>
                </div>
              </div>
            ))}
      </div>
    </div>
  );
}
