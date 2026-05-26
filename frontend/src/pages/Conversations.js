import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getConversations } from "../api";
import { Filter } from "lucide-react";

export default function Conversations() {
  const [page, setPage] = useState(1);
  const [intent, setIntent] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [failuresOnly, setFailuresOnly] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["conversations", page, intent, sentiment, failuresOnly],
    queryFn: () => getConversations({ page, limit: 25, intent, sentiment, failures_only: failuresOnly }),
    keepPreviousData: true,
  });

  const conversations = data?.conversations || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 25);

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Conversations</div>
        <div className="page-sub">{total} total · filter and explore all logged chats</div>
      </div>

      <div className="filters-row">
        <Filter size={13} style={{ color: "var(--text3)" }} />
        <button className={`filter-btn ${!failuresOnly && !sentiment && !intent ? "active" : ""}`}
          onClick={() => { setIntent(""); setSentiment(""); setFailuresOnly(false); setPage(1); }}>
          All
        </button>
        <button className={`filter-btn ${failuresOnly ? "active" : ""}`}
          onClick={() => { setFailuresOnly(!failuresOnly); setPage(1); }}>
          Failures only
        </button>
        {["positive", "neutral", "negative"].map(s => (
          <button key={s} className={`filter-btn ${sentiment === s ? "active" : ""}`}
            onClick={() => { setSentiment(sentiment === s ? "" : s); setPage(1); }}>
            {s}
          </button>
        ))}
      </div>

      <div className="panel-full" style={{ padding: 0 }}>
        {isLoading
          ? <div className="loading"><div className="spinner" />Loading...</div>
          : <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ paddingLeft: 20 }}>User Message</th>
                  <th>Agent Response</th>
                  <th>Intent</th>
                  <th>Sentiment</th>
                  <th>Status</th>
                  <th style={{ paddingRight: 20 }}>Session</th>
                </tr>
              </thead>
              <tbody>
                {conversations.map(c => (
                  <tr key={c.id}>
                    <td style={{ paddingLeft: 20 }}>
                      <div style={{ maxWidth: 260, fontSize: 13 }}>{c.user_message}</div>
                    </td>
                    <td>
                      <div style={{ maxWidth: 260, fontSize: 13, color: "var(--text2)" }}>
                        {c.agent_response?.slice(0, 120)}{c.agent_response?.length > 120 ? "…" : ""}
                      </div>
                      {c.is_failure && c.failure_reason && (
                        <div style={{ fontSize: 11, color: "var(--red)", marginTop: 4 }}>
                          ↳ {c.failure_reason}
                        </div>
                      )}
                    </td>
                    <td>{c.intent ? <span className="badge badge-intent">{c.intent}</span> : <span style={{ color: "var(--text3)" }}>—</span>}</td>
                    <td>{c.sentiment ? <span className={`badge badge-${c.sentiment}`}>{c.sentiment}</span> : "—"}</td>
                    <td>{c.is_failure
                      ? <span className="badge badge-failure">✗ fail</span>
                      : c.analyzed
                        ? <span style={{ color: "var(--accent)", fontSize: 11 }}>✓ ok</span>
                        : <span style={{ color: "var(--text3)", fontSize: 11 }}>pending</span>
                    }</td>
                    <td style={{ paddingRight: 20, fontFamily: "IBM Plex Mono", fontSize: 11, color: "var(--text3)" }}>
                      {c.session_id?.slice(0, 8)}…
                    </td>
                  </tr>
                ))}
                {conversations.length === 0 && (
                  <tr><td colSpan={6} className="empty-state">No conversations match this filter</td></tr>
                )}
              </tbody>
            </table>
          </div>
        }

        {totalPages > 1 && (
          <div className="pagination" style={{ padding: "12px 20px" }}>
            <button className="btn btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
              ← Prev
            </button>
            <span style={{ color: "var(--text3)", fontFamily: "IBM Plex Mono", fontSize: 12 }}>
              {page} / {totalPages}
            </span>
            <button className="btn btn-ghost" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
