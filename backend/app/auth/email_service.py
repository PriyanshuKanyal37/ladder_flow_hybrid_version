import logging
import os

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")
_FROM = os.getenv("FROM_EMAIL", "noreply@ladderflow.com")
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def send_password_reset_email(email: str, token: str) -> None:
    reset_url = f"{_FRONTEND_URL}/reset-password?token={token}"
    try:
        resend.Emails.send({
            "from": _FROM,
            "to": email,
            "subject": "Reset your Ladder Flow password",
            "html": f"""
<div style="font-family:-apple-system,sans-serif;max-width:480px;margin:40px auto;padding:32px;
            background:#111;border:1px solid #222;border-radius:12px;">
  <p style="margin:0 0 4px;font-size:18px;font-weight:700;color:#fff;">Ladder Flow</p>
  <hr style="border:none;border-top:1px solid #222;margin:16px 0 24px;">
  <h2 style="margin:0 0 12px;color:#fff;font-size:20px;font-weight:700;">Reset your password</h2>
  <p style="color:#aaa;font-size:14px;line-height:1.6;margin:0 0 24px;">
    We received a request to reset your password. This link expires in&nbsp;<strong style="color:#fff;">1&nbsp;hour</strong>.
  </p>
  <a href="{reset_url}"
     style="display:inline-block;background:#e95335;color:#fff;padding:12px 28px;
            border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    Reset Password
  </a>
  <p style="color:#555;font-size:11px;margin-top:32px;line-height:1.5;">
    If you didn&apos;t request this, you can safely ignore this email.<br>
    Your password won&apos;t change until you click the link above.
  </p>
</div>
""",
        })
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", email, exc)
