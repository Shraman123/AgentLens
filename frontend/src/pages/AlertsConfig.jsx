import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Send, Check } from "lucide-react";
import { getAlertConfig, updateAlertConfig, testAlert } from "../api.js";

export default function AlertsConfig() {
  const qc = useQueryClient();
  const [toast, setToast] = useState(null);
  const { data, isLoading } = useQuery({ queryKey: ["alertConfig"], queryFn: getAlertConfig });

  const [threshold, setThreshold] = useState(20);
  const [minConvs, setMinConvs] = useState(10);
  const [emailAlerts, setEmailAlerts] = useState(true);

  useEffect(() => {
    if (data) {
      setThreshold(data.failure_rate_threshold ?? 20);
      setMinConvs(data.min_conversations ?? 10);
      setEmailAlerts(data.email_alerts ?? true);
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () => updateAlertConfig({ failure_rate_threshold: threshold, min_conversations: minConvs, email_alerts: emailAlerts }),
    onSuccess: () => { qc.invalidateQueries(["alertConfig"]); showToast("Alert config saved", "success"); },
    onError: () => showToast("Failed to save", "error"),
  });

  const sendTest = useMutation({
    mutationFn: testAlert,
    onSuccess: () => showToast("Test alert sent — check your inbox", "success"),
    onError: () => showToast("Failed to send test alert. Check RESEND_API_KEY.", "error"),
  });

  function showToast(msg, type) { setToast({ msg, type }); setTimeout(() => setToast(null), 3500); }

  return (
    <div>
      {toast && <div className={`toast ${toast.type}`}>{toast.msg}</div>}
      <div className="page-header">
        <div className="page-title">Alert Configuration</div>
        <div className="page-sub">Get emailed when your agent's failure rate spikes above a threshold</div>
      </div>

      <div className="alerts-layout">
        <div className="panel">
          <div className="panel-title"><Bell size={13} /> Alert Rules</div>

          {isLoading
            ? <div className="skeleton" style={{ height: 200 }} />
            : <div className="alert-fields">
              <div className="field">
                <label className="field-label">Failure Rate Threshold (%)</label>
                <div className="field-sub">Send an alert when failure rate exceeds this value</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
                  <input
                    type="range" min={5} max={80} step={5}
                    value={threshold}
                    onChange={e => setThreshold(Number(e.target.value))}
                    className="range-input"
                  />
                  <span className="range-val">{threshold}%</span>
                </div>
              </div>

              <div className="field">
                <label className="field-label">Minimum Conversations</label>
                <div className="field-sub">Only alert if there are at least this many conversations logged</div>
                <input
                  type="number" min={5} max={500} step={5}
                  value={minConvs}
                  onChange={e => setMinConvs(Number(e.target.value))}
                  className="field-input"
                  style={{ marginTop: 8, width: 120 }}
                />
              </div>

              <div className="field">
                <label className="field-label toggle-label">
                  <span>Email Alerts</span>
                  <button
                    className={`toggle ${emailAlerts ? "on" : "off"}`}
                    onClick={() => setEmailAlerts(!emailAlerts)}
                    aria-label="Toggle email alerts"
                  >
                    <span className="toggle-knob" />
                  </button>
                </label>
                <div className="field-sub">Requires RESEND_API_KEY set in HF Space secrets</div>
              </div>

              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <button className="btn btn-primary" onClick={() => save.mutate()} disabled={save.isPending}>
                  {save.isPending ? <span className="spinner" style={{ margin: 0, width: 12, height: 12, borderWidth: 2 }} /> : <Check size={13} />}
                  Save Config
                </button>
                <button className="btn btn-ghost" onClick={() => sendTest.mutate()} disabled={sendTest.isPending}>
                  <Send size={13} /> Send Test Alert
                </button>
              </div>
            </div>}
        </div>

        <div className="panel">
          <div className="panel-title">How Alerts Work</div>
          <div className="how-it-works">
            <div className="how-step">
              <div className="how-step-n">1</div>
              <div>
                <div className="how-step-title">Scheduler runs every hour</div>
                <div className="how-step-sub">APScheduler auto-analyzes all new conversations for every project</div>
              </div>
            </div>
            <div className="how-step">
              <div className="how-step-n">2</div>
              <div>
                <div className="how-step-title">Failure rate is calculated</div>
                <div className="how-step-sub">After analysis, the overall failure rate is compared to your threshold</div>
              </div>
            </div>
            <div className="how-step">
              <div className="how-step-n">3</div>
              <div>
                <div className="how-step-title">Email is sent via Resend</div>
                <div className="how-step-sub">You get a detailed email with failure rate, total count, and sample failures</div>
              </div>
            </div>
            <div className="how-step">
              <div className="how-step-n">4</div>
              <div>
                <div className="how-step-title">Fix & monitor</div>
                <div className="how-step-sub">Use Prompt Lab to fix the failures, then watch the rate drop</div>
              </div>
            </div>
          </div>

          <div className="alert-prereq">
            <div className="prereq-title">Required setup</div>
            <code className="prereq-code">RESEND_API_KEY=re_...</code>
            <div className="prereq-sub">Add to HF Space secrets → Settings → Variables and secrets</div>
          </div>
        </div>
      </div>
    </div>
  );
}
