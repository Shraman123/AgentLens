import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, X, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { getConversations, exportCsvUrl } from "../api.js";

function Modal({ conv, onClose }) {
  if (!conv) return null;
  let meta = {};
  try { meta = JSON.parse(conv.metadata || "{}"); } catch {}
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Conversation Detail</div>
          <button className="modal-close" onClick={onClose}><X size={14} /></button>
        </div>
        <div className="modal-body">
          <div className="conv-meta-row">
            <span className="meta-chip">Session: {conv.session_id?.slice(0, 12)}…</span>
            {conv.intent && <span className="badge badge-intent">{conv.intent}</span>}
            {conv.sentiment && <span className={`badge badge-${conv.sentiment}`}>{conv.sentiment}</span>}
            {conv.is_failure && <span className="badge badge-failure">failure</span>}
            {meta.latency_ms && <span className="meta-chip">{meta.latency_ms}ms</span>}
            {meta.model && <span className="meta-chip model">{meta.model}</span>}
          </div>
          <div className="conv-block user">
            <div className="conv-block-label">User</div>
            <div className="conv-block-text">{conv.user_message}</div>
          </div>
          <div className="conv-block agent">
            <div className="conv-block-label">Agent</div>
            <div className="conv-block-text">{conv.agent_response}</div>
          </div>
          {conv.is_failure && conv.failure_reason && (
            <div className="conv-failure-reason">
              <span className="failure-label">Failure reason:</span> {conv.failure_reason}
            </div>
          )}
          <div className="conv-time">{conv.created_at ? new Date(conv.created_at).toLocaleString() : "—"}</div>
        </div>
      </div>
    </div>
  );
}

export default function Conversations() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [selected, setSelected] = useState(null);
  const LIMIT = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["convs", page, search, sentiment, failuresOnly],
    queryFn: () => getConversations({ page, limit: LIMIT, search, sentiment: sentiment || undefined, failures_only: failuresOnly }),
    keepPreviousData: true,
  });

  const convs = data?.conversations || [];
  const total = data?.total || 0;
  const pages = Math.ceil(total / LIMIT);

  return (
    <div>
      <Modal conv={selected} onClose={() => setSelected(null)} />
      <div className="page-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="page-title">Conversations</div>
            <div className="page-sub">{total} total · click any row to inspect</div>
          </div>
          <a href={exportCsvUrl(failuresOnly)} download className="btn btn-ghost">
            <Download size={13} /> Export CSV
          </a>
        </div>
      </div>

      <div className="filter-bar">
        <div className="search-wrap">
          <Search size={13} className="search-icon" />
          <input className="search-input" placeholder="Search messages…" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          {search && <button className="search-clear" onClick={() => setSearch("")}><X size={12} /></button>}
        </div>
        <div className="filter-pills">
          {["", "positive", "neutral", "negative"].map(s => (
            <button key={s} className={`filter-pill ${sentiment === s ? "active" : ""}`} onClick={() => { setSentiment(s); setPage(1); }}>
              {s || "All sentiments"}
            </button>
          ))}
          <button className={`filter-pill ${failuresOnly ? "active red" : ""}`} onClick={() => { setFailuresOnly(!failuresOnly); setPage(1); }}>
            Failures only
          </button>
        </div>
      </div>

      <div className="panel-full" style={{ marginTop: 0 }}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>User Message</th>
                <th>Agent Response</th>
                <th>Intent</th>
                <th>Sentiment</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array(10).fill(0).map((_, i) => (
                  <tr key={i}>{Array(7).fill(0).map((_, j) => <td key={j}><div className="skeleton" style={{ height: 14 }} /></td>)}</tr>
                ))
                : convs.map(c => {
                  let meta = {}; try { meta = JSON.parse(c.metadata || "{}"); } catch {}
                  return (
                    <tr key={c.id} className="clickable-row" onClick={() => setSelected(c)}>
                      <td className="msg-cell" title={c.user_message}>{c.user_message}</td>
                      <td className="msg-cell" title={c.agent_response}>{c.agent_response}</td>
                      <td>{c.intent ? <span className="badge badge-intent">{c.intent}</span> : <span className="dim">—</span>}</td>
                      <td>{c.sentiment ? <span className={`badge badge-${c.sentiment}`}>{c.sentiment}</span> : "—"}</td>
                      <td>{c.is_failure ? <span className="badge badge-failure">failure</span> : <span className="ok-text">✓</span>}</td>
                      <td className="time-cell">{meta.latency_ms ? `${meta.latency_ms}ms` : "—"}</td>
                      <td className="time-cell">{c.created_at ? new Date(c.created_at).toLocaleTimeString() : "—"}</td>
                    </tr>
                  );
                })}
              {!isLoading && convs.length === 0 && (
                <tr><td colSpan={7} className="empty-state">No conversations match your filters</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {pages > 1 && (
          <div className="pagination">
            <button className="pg-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={14} /></button>
            <span className="pg-info">Page {page} of {pages}</span>
            <button className="pg-btn" disabled={page >= pages} onClick={() => setPage(p => p + 1)}><ChevronRight size={14} /></button>
          </div>
        )}
      </div>
    </div>
  );
}
