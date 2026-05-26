import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { suggestPrompt } from "../api";
import { Wand2, Copy, Check } from "lucide-react";

export default function PromptLab() {
  const [currentPrompt, setCurrentPrompt] = useState("");
  const [copied, setCopied] = useState(false);

  const suggest = useMutation({
    mutationFn: () => suggestPrompt(currentPrompt),
  });

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Prompt Lab</div>
        <div className="page-sub">
          Paste your current system prompt. AI will analyze your failure patterns and suggest improvements.
        </div>
      </div>

      <div className="panel-full">
        <div className="panel-title">Current System Prompt</div>
        <textarea
          className="prompt-textarea"
          placeholder="You are a helpful assistant that..."
          value={currentPrompt}
          onChange={e => setCurrentPrompt(e.target.value)}
          rows={8}
        />
        <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
          <button
            className="btn btn-primary"
            onClick={() => suggest.mutate()}
            disabled={suggest.isPending}
          >
            {suggest.isPending
              ? <><div className="spinner" style={{ margin: 0, width: 12, height: 12, borderWidth: 2 }} /> Analyzing failures...</>
              : <><Wand2 size={14} /> Suggest Improvements</>
            }
          </button>
          <span style={{ color: "var(--text3)", fontSize: 12 }}>
            Uses your recent failure patterns to improve the prompt
          </span>
        </div>
      </div>

      {suggest.isError && (
        <div className="panel-full" style={{ borderColor: "rgba(255,68,68,0.2)" }}>
          <div style={{ color: "var(--red)", fontSize: 13 }}>
            ✗ Failed to generate suggestion. Make sure your backend is running and ANTHROPIC_API_KEY is set.
          </div>
        </div>
      )}

      {suggest.data && (
        <div className="panel-full">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <div className="panel-title" style={{ marginBottom: 0 }}>Suggested Prompt</div>
            <button
              className="btn btn-ghost"
              style={{ fontSize: 12 }}
              onClick={() => handleCopy(suggest.data.suggested_prompt)}
            >
              {copied ? <><Check size={13} /> Copied!</> : <><Copy size={13} /> Copy</>}
            </button>
          </div>
          <div className="suggestion-box">
            <div className="suggestion-label">✦ AI SUGGESTED</div>
            <pre style={{
              fontFamily: "IBM Plex Mono",
              fontSize: 13,
              color: "var(--text)",
              whiteSpace: "pre-wrap",
              lineHeight: 1.7
            }}>
              {suggest.data.suggested_prompt}
            </pre>
          </div>

          {suggest.data.reasoning && (
            <div>
              <div className="panel-title" style={{ marginTop: 16, marginBottom: 8 }}>Reasoning</div>
              <div className="reasoning-box">{suggest.data.reasoning}</div>
            </div>
          )}

          <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
            <button className="btn btn-primary" onClick={() => setCurrentPrompt(suggest.data.suggested_prompt)}>
              Apply to editor
            </button>
            <button className="btn btn-ghost" onClick={() => suggest.mutate()}>
              Regenerate
            </button>
          </div>
        </div>
      )}

      {!suggest.data && !suggest.isPending && (
        <div className="panel-full" style={{ textAlign: "center", padding: "48px 24px" }}>
          <div style={{ color: "var(--text3)", fontFamily: "IBM Plex Mono", fontSize: 13, lineHeight: 2 }}>
            <div style={{ fontSize: 24, marginBottom: 12 }}>⚡</div>
            Paste your system prompt above and click Suggest Improvements.<br />
            The AI will analyze your logged failures and tell you exactly what to fix.
          </div>
        </div>
      )}
    </div>
  );
}
