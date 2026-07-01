import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Wand2, Copy, Check, RefreshCw } from "lucide-react";
import { suggestPrompt } from "../api.js";

export default function PromptLab() {
  const [current, setCurrent] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const suggest = useMutation({
    mutationFn: () => suggestPrompt(current),
    onSuccess: setResult,
  });

  function copy(text) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Prompt Lab</div>
        <div className="page-sub">Paste your current system prompt — get AI-generated improvements based on real failure patterns</div>
      </div>

      <div className="prompt-layout">
        <div className="panel">
          <div className="panel-title">Current System Prompt</div>
          <textarea
            className="prompt-textarea"
            placeholder={"You are a helpful assistant...\n\nPaste your current system prompt here. AgentLens will analyze your failure patterns and suggest targeted improvements."}
            value={current}
            onChange={e => setCurrent(e.target.value)}
            rows={14}
          />
          <button
            className="btn btn-primary"
            style={{ marginTop: 12, width: "100%" }}
            onClick={() => suggest.mutate()}
            disabled={suggest.isPending || !current.trim()}
          >
            {suggest.isPending
              ? <><span className="spinner" style={{ margin: 0, width: 13, height: 13, borderWidth: 2 }} /> Analyzing failures & generating…</>
              : <><Wand2 size={14} /> Suggest Improvements</>}
          </button>
        </div>

        <div className="panel">
          <div className="panel-title" style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Suggested Prompt</span>
            {result && (
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-ghost btn-sm" onClick={() => copy(result.suggested_prompt)}>
                  {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => suggest.mutate()}>
                  <RefreshCw size={12} /> Regenerate
                </button>
              </div>
            )}
          </div>

          {suggest.isPending && (
            <div className="prompt-loading">
              <div className="spinner" />
              <span>Analyzing {`>`}100 failure patterns…</span>
            </div>
          )}

          {suggest.isError && (
            <div className="login-error">Failed to generate suggestions. Make sure you have analyzed conversations first.</div>
          )}

          {result && !suggest.isPending && (
            <>
              <pre className="prompt-result">{result.suggested_prompt}</pre>
              {result.reasoning?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div className="panel-title" style={{ fontSize: 11, marginBottom: 8 }}>Why these changes</div>
                  <ul className="reasoning-list">
                    {result.reasoning.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </>
          )}

          {!result && !suggest.isPending && (
            <div className="empty-state" style={{ minHeight: 200, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
              <Wand2 size={24} style={{ color: "var(--text3)" }} />
              <div>Suggestions will appear here</div>
              <div style={{ fontSize: 11, color: "var(--text3)" }}>Requires analyzed conversations to detect failure patterns</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
