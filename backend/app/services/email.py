import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import AlertSubscriber, AlertLog

logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_email(to_email: str, subject: str, body_html: str):
    """Send a real email via Gmail SMTP SSL."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Skipping email send.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


async def check_alerts_and_notify(
    db: AsyncSession,
    rain_prob: float,
    temp: float,
    humidity: float,
    pressure: float
):
    alerts_triggered = []

    if rain_prob > 70:
        alerts_triggered.append(("🌧️ Rain Alert", f"Rain probability is <b>{rain_prob:.1f}%</b> — prepare for rain!"))
    if temp > 35:
        alerts_triggered.append(("🌡️ Heat Alert", f"Temperature is <b>{temp:.1f}°C</b> — extreme heat warning!"))
    if humidity > 90:
        alerts_triggered.append(("💧 Humidity Alert", f"Humidity is <b>{humidity:.1f}%</b> — very high moisture levels!"))
    if pressure < 980:
        alerts_triggered.append(("⚠️ Low Pressure Alert", f"Pressure is <b>{pressure:.1f} hPa</b> — storm possible!"))

    if not alerts_triggered:
        return

    # Get subscribers
    result = await db.execute(select(AlertSubscriber).where(AlertSubscriber.is_active == True))
    subscribers = result.scalars().all()

    if not subscribers:
        return

    # Build alert rows for HTML email
    rows_html = "".join(
        f"<tr><td style='padding:10px;font-size:18px;'>{icon}</td>"
        f"<td style='padding:10px;color:#e2e8f0;'>{msg}</td></tr>"
        for icon, msg in alerts_triggered
    )
    plain_message = " | ".join(f"{icon}: {msg}" for icon, msg in alerts_triggered)

    html_body = f"""
    <div style="font-family:Inter,sans-serif;background:#0f172a;padding:32px;border-radius:16px;">
      <h1 style="color:#38bdf8;margin-bottom:6px;">🌩️ Nexus Weather AI - Alert</h1>
      <p style="color:#94a3b8;margin-top:0;">The following thresholds have been exceeded:</p>
      <table style="width:100%;border-collapse:collapse;background:#1e293b;border-radius:12px;overflow:hidden;">
        {rows_html}
      </table>
      <p style="color:#64748b;font-size:12px;margin-top:24px;">
        This is an automated alert from your IoT Weather Station.<br>
        To unsubscribe, visit your dashboard.
      </p>
    </div>
    """

    subject = f"⚠️ Weather Alert: {', '.join(t[0] for t in alerts_triggered)}"

    for sub in subscribers:
        send_email(sub.email, subject, html_body)

        alert_log = AlertLog(
            alert_type="Threshold Breach",
            message=plain_message,
            sent_to=sub.email
        )
        db.add(alert_log)

    await db.commit()
