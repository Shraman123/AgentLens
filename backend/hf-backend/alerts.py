import httpx
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = "AgentLens <onboarding@resend.dev>"  # use resend default until domain verified

async def send_failure_alert(
    to_email: str,
    project_name: str,
    failure_rate: float,
    total: int,
    failures: int,
    top_failures: list
):
    """Send email alert when failure rate spikes."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email alert")
        return

    failure_list = "\n".join([
        f"• {f.get('user_message', '')[:80]} → {f.get('failure_reason', 'unknown')}"
        for f in top_failures[:5]
    ]) or "No details available"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #e8e8e8; margin: 0; padding: 0; }}
      .container {{ max-width: 560px; margin: 40px auto; padding: 0 20px; }}
      .header {{ background: #111; border: 1px solid #222; border-radius: 8px 8px 0 0; padding: 24px; border-bottom: none; }}
      .logo {{ color: #00ff88; font-family: monospace; font-size: 18px; font-weight: 700; margin-bottom: 4px; }}
      .body {{ background: #111; border: 1px solid #222; border-radius: 0 0 8px 8px; padding: 24px; }}
      .alert-box {{ background: rgba(255,68,68,0.08); border: 1px solid rgba(255,68,68,0.2); border-radius: 6px; padding: 16px; margin-bottom: 20px; }}
      .alert-title {{ color: #ff4444; font-size: 16px; font-weight: 700; margin-bottom: 4px; }}
      .alert-sub {{ color: #888; font-size: 13px; }}
      .stat-row {{ display: flex; gap: 12px; margin-bottom: 20px; }}
      .stat {{ background: #161616; border: 1px solid #222; border-radius: 6px; padding: 12px 16px; flex: 1; }}
      .stat-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #555; font-family: monospace; margin-bottom: 4px; }}
      .stat-val {{ font-size: 24px; font-weight: 700; font-family: monospace; }}
      .failures-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #555; font-family: monospace; margin-bottom: 10px; }}
      .failure-item {{ background: #161616; border-left: 2px solid #ff4444; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 4px 4px 0; font-size: 13px; color: #aaa; }}
      .cta {{ display: block; text-align: center; background: #00ff88; color: #000; padding: 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 14px; margin-top: 20px; }}
      .footer {{ text-align: center; margin-top: 20px; font-size: 11px; color: #444; font-family: monospace; }}
    </style>
    </head>
    <body>
    <div class="container">
      <div class="header">
        <div class="logo">⚡ AgentLens</div>
        <div style="color:#555;font-size:13px;">Failure Rate Alert</div>
      </div>
      <div class="body">
        <div class="alert-box">
          <div class="alert-title">🔴 High Failure Rate Detected</div>
          <div class="alert-sub">Project: <strong style="color:#e8e8e8">{project_name}</strong> · {datetime.utcnow().strftime('%b %d, %Y %H:%M UTC')}</div>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px">
          <tr>
            <td width="33%" style="padding:8px">
              <div style="background:#161616;border:1px solid #222;border-radius:6px;padding:12px 16px">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#555;font-family:monospace;margin-bottom:4px">Failure Rate</div>
                <div style="font-size:24px;font-weight:700;font-family:monospace;color:#ff4444">{failure_rate}%</div>
              </div>
            </td>
            <td width="33%" style="padding:8px">
              <div style="background:#161616;border:1px solid #222;border-radius:6px;padding:12px 16px">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#555;font-family:monospace;margin-bottom:4px">Total Chats</div>
                <div style="font-size:24px;font-weight:700;font-family:monospace;color:#00ff88">{total}</div>
              </div>
            </td>
            <td width="33%" style="padding:8px">
              <div style="background:#161616;border:1px solid #222;border-radius:6px;padding:12px 16px">
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#555;font-family:monospace;margin-bottom:4px">Failures</div>
                <div style="font-size:24px;font-weight:700;font-family:monospace;color:#ffcc00">{failures}</div>
              </div>
            </td>
          </tr>
        </table>

        <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#555;font-family:monospace;margin-bottom:10px">Recent Failures</div>
        {''.join([f'<div style="background:#161616;border-left:2px solid #ff4444;padding:8px 12px;margin-bottom:6px;border-radius:0 4px 4px 0;font-size:13px;color:#aaa">{f.get("user_message","")[:80]}</div>' for f in top_failures[:5]])}

        <a href="https://agent-lens-two.vercel.app" style="display:block;text-align:center;background:#00ff88;color:#000;padding:12px;border-radius:6px;text-decoration:none;font-weight:700;font-size:14px;margin-top:20px">
          View Dashboard →
        </a>
      </div>
      <div style="text-align:center;margin-top:20px;font-size:11px;color:#444;font-family:monospace">
        AgentLens · You're receiving this because your failure rate exceeded 20%<br>
      </div>
    </div>
    </body>
    </html>
    """

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": FROM_EMAIL,
                    "to": [to_email],
                    "subject": f"🔴 [{project_name}] Failure rate spiked to {failure_rate}%",
                    "html": html
                },
                timeout=10.0
            )
            if r.status_code == 200:
                logger.info(f"Alert email sent to {to_email}")
            else:
                logger.error(f"Failed to send email: {r.text}")
    except Exception as e:
        logger.error(f"Email error: {e}")
