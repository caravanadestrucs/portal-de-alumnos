"""
Mail util for bulk credential delivery.
Uses smtplib + email.mime, mocks when MAIL_SERVER not configured.
Never logs plaintext temp password.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _get_smtp_config():
    """Resolve SMTP config: .env MAIL_* first, fallback to DB Config."""
    # Try Flask app config if available
    try:
        from flask import current_app
        if current_app:
            cfg = current_app.config
            server = cfg.get("MAIL_SERVER") or cfg.get("MAIL_HOST") or ""
            if server:
                return {
                    "host": server,
                    "port": int(cfg.get("MAIL_PORT", 587)),
                    "user": cfg.get("MAIL_USERNAME") or cfg.get("MAIL_USER") or "",
                    "password": cfg.get("MAIL_PASSWORD", ""),
                    "use_tls": bool(cfg.get("MAIL_USE_TLS", True)),
                    "sender": cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("MAIL_USERNAME") or "",
                }
    except Exception:
        pass

    # Fallback to env directly
    server = os.environ.get("MAIL_SERVER") or os.environ.get("MAIL_HOST") or ""
    if server:
        return {
            "host": server,
            "port": int(os.environ.get("MAIL_PORT", "587") or 587),
            "user": os.environ.get("MAIL_USERNAME") or os.environ.get("MAIL_USER") or "",
            "password": os.environ.get("MAIL_PASSWORD", ""),
            "use_tls": os.environ.get("MAIL_USE_TLS", "true").lower() == "true",
            "sender": os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME") or "",
        }

    # Fallback to DB Config table
    try:
        from models import Config
        configs = {c.key: c.value for c in Config.query.all()}
        host = configs.get("smtp_host") or configs.get("MAIL_SERVER") or ""
        if host:
            return {
                "host": host,
                "port": int(configs.get("smtp_port", "587") or 587),
                "user": configs.get("smtp_email") or configs.get("smtp_user") or "",
                "password": configs.get("smtp_password", ""),
                "use_tls": (configs.get("smtp_use_tls", "true").lower() == "true"),
                "sender": configs.get("smtp_email") or "",
            }
    except Exception:
        pass

    return {"host": "", "port": 587, "user": "", "password": "", "use_tls": True, "sender": ""}


def render_credentials_email(temp_password: str, login_url: str = "", app_name: str = "Portal de Calificaciones") -> str:
    """Render HTML for credentials email (ES, inline styles). Does NOT log."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8" /></head>
<body style="margin:0;padding:0;background:#f4f7fa;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fa;min-width:100%;">
<tr><td align="center" style="padding:40px 20px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1a365d 0%,#2b6cb0 100%);padding:32px 40px;text-align:center;">
<h1 style="color:#fff;font-size:24px;margin:0;">{app_name}</h1>
<h2 style="color:#fff;font-size:18px;margin:10px 0 0 0;">Tus credenciales de acceso</h2>
</td></tr>
<tr><td style="padding:40px;">
<p style="color:#2d3748;font-size:16px;">Has recibido tus credenciales para acceder al portal.</p>
<p style="color:#2d3748;font-size:14px;">Usuario: <strong>tu email registrado</strong></p>
<div style="background:#ebf4ff;padding:16px;border-radius:8px;text-align:center;margin:20px 0;">
<p style="margin:0;color:#2b6cb0;font-size:14px;">Contraseña temporal:</p>
<p style="margin:8px 0 0 0;color:#1a365d;font-size:22px;font-weight:700;letter-spacing:2px;">{temp_password}</p>
<p style="margin:8px 0 0 0;color:#718096;font-size:12px;">Expira en 24 horas — deberás cambiarla al iniciar sesión.</p>
</div>
{f'<p style="text-align:center;"><a href="{login_url}" style="display:inline-block;background:#2b6cb0;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">Iniciar sesión</a></p>' if login_url else ''}
<p style="color:#718096;font-size:13px;margin-top:24px;">Si no solicitaste este correo, ignoralo.</p>
</td></tr>
<tr><td style="background:#edf2f7;padding:20px;text-align:center;"><p style="color:#4a5568;font-size:12px;margin:0;">&copy; 2026 Universidad Felipe Villanueva</p></td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def send_credentials_email(to_email: str, temp_password: str, alumno_nombre: str = "", login_url: str = "") -> dict:
    """
    Send credentials email via smtplib.
    Signature supports (to_email, temp_password, alumno_nombre) and (to_email, temp_password, login_url) compat.
    Returns {"success": bool, "error": str}
    Never raises, never logs plaintext temp_password.
    If MAIL_SERVER not configured, logs warning and returns success=True (mock for dev/tests).
    """
    # Normalize alumno_nombre vs login_url overload: if alumno_nombre looks like URL, treat as login_url
    if alumno_nombre and alumno_nombre.startswith("http"):
        login_url = alumno_nombre
        alumno_nombre = ""

    # Mock if no SMTP config
    cfg = _get_smtp_config()
    if not cfg.get("host") or not cfg.get("user"):
        logger.info(f"[MAIL MOCK] would send credentials to {to_email} (no SMTP configured)")
        # Still render to validate template, but don't send
        try:
            _ = render_credentials_email(temp_password, login_url)
        except Exception:
            pass
        return {"success": True}

    try:
        html_body = render_credentials_email(temp_password, login_url)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Tus credenciales de acceso - Portal FV"
        msg["From"] = cfg.get("sender") or cfg.get("user")
        msg["To"] = to_email
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        server = smtplib.SMTP(host=cfg["host"], port=int(cfg["port"]), timeout=10)
        if cfg.get("use_tls"):
            server.starttls()
        if cfg.get("password"):
            server.login(cfg["user"], cfg["password"])
        server.send_message(msg)
        server.quit()
        logger.info(f"Credentials email sent to {to_email}")
        return {"success": True}
    except Exception as e:
        # Never include temp_password in log
        logger.error(f"Failed to send credentials email to {to_email}: {str(e)}")
        return {"success": False, "error": str(e)}
