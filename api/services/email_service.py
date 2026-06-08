"""
SMTP email service.
Sends real emails when SMTP_HOST is configured, logs to console otherwise.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send(self, to: str, subject: str, html_body: str, text_body: str = "") -> None:
        if not settings.SMTP_HOST:
            logger.info("[EMAIL — no SMTP configured] To: %s | Subject: %s", to, subject)
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.ehlo()
                if settings.SMTP_PORT == 587:
                    server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.FROM_EMAIL, [to], msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            raise


class PasswordResetService:
    """Manages one-time password-reset tokens stored in Redis."""

    TOKEN_TTL = 3600  # 1 hour

    def __init__(self):
        import redis as redis_lib
        self._redis = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)

    def _key(self, token: str) -> str:
        return f"pwd_reset:{token}"

    def create_token(self, user_id: str) -> str:
        from ..utils.security import generate_reset_token
        token = generate_reset_token()
        self._redis.setex(self._key(token), self.TOKEN_TTL, user_id)
        return token

    def verify_token(self, token: str) -> str | None:
        """Returns user_id if valid, None if expired/invalid."""
        return self._redis.get(self._key(token))

    def consume_token(self, token: str) -> str | None:
        """One-time use: returns user_id and deletes the token."""
        user_id = self._redis.get(self._key(token))
        if user_id:
            self._redis.delete(self._key(token))
        return user_id
