"""Celery tasks for async email delivery."""
import logging
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="api.tasks.email_tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_email_task(self, to: str, subject: str, html_body: str, text_body: str = ""):
    try:
        from ..services.email_service import EmailService
        EmailService().send(to=to, subject=subject, html_body=html_body, text_body=text_body)
        logger.info("Email sent to %s: %s", to, subject)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.warning("Email send failed, retrying: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(name="api.tasks.email_tasks.send_welcome_email")
def send_welcome_email_task(to: str, full_name: str):
    html = f"""
    <h2>Welcome to BR Matching System, {full_name}!</h2>
    <p>Your account has been created. You can now log in and start evaluating proposals.</p>
    <p><a href="http://localhost:3000/login">Log in now →</a></p>
    """
    send_email_task.delay(to=to, subject="Welcome to BR Match", html_body=html)


@celery_app.task(name="api.tasks.email_tasks.send_password_reset_email")
def send_password_reset_email_task(to: str, reset_token: str, base_url: str = "http://localhost:3000"):
    link = f"{base_url}/reset-password?token={reset_token}"
    html = f"""
    <h2>Password Reset Request</h2>
    <p>Click the link below to reset your password. This link expires in 1 hour.</p>
    <p><a href="{link}">Reset Password →</a></p>
    <p>If you did not request this, ignore this email.</p>
    """
    send_email_task.delay(to=to, subject="BR Match — Password Reset", html_body=html)


@celery_app.task(name="api.tasks.email_tasks.send_match_completed_email")
def send_match_completed_email_task(to: str, vendor_name: str, overall_score: float, proposal_id: str, base_url: str = "http://localhost:3000"):
    pct = round(overall_score * 100, 1)
    link = f"{base_url}/proposals/{proposal_id}/analysis"
    html = f"""
    <h2>Matching Complete — {vendor_name}</h2>
    <p>The AI matching analysis for <strong>{vendor_name}</strong>'s proposal is ready.</p>
    <p><strong>Overall Match Score: {pct}%</strong></p>
    <p><a href="{link}">View Full Analysis →</a></p>
    """
    send_email_task.delay(to=to, subject=f"Match Complete: {vendor_name} — {pct}%", html_body=html)


@celery_app.task(name="api.tasks.email_tasks.send_lockout_alert_email")
def send_lockout_alert_email_task(to: str, ip_address: str):
    html = f"""
    <h2>Security Alert — Account Temporarily Locked</h2>
    <p>Your account has been temporarily locked due to multiple failed login attempts.</p>
    <p><strong>IP Address:</strong> {ip_address}</p>
    <p>If this was you, please wait 30 minutes and try again.</p>
    <p>If this was not you, please contact support immediately.</p>
    """
    send_email_task.delay(to=to, subject="BR Match — Security Alert: Account Locked", html_body=html)
