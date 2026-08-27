"""
Utilidad de envío de emails usando smtplib (stdlib)
Lee configuración SMTP desde el modelo Config en DB
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _get_smtp_config():
    """
    Lee la configuración SMTP desde el modelo Config en DB.
    Retorna un dict con las claves smtp_* o valores vacíos si no existen.
    """
    from models import Config
    
    configs = Config.query.all()
    cfg = {c.key: c.value for c in configs}
    
    return {
        'smtp_host': cfg.get('smtp_host', ''),
        'smtp_port': cfg.get('smtp_port', '587'),
        'smtp_email': cfg.get('smtp_email', ''),
        'smtp_password': cfg.get('smtp_password', ''),
        'smtp_use_tls': cfg.get('smtp_use_tls', 'true'),
    }


def send_email(to_email: str, subject: str, html_body: str) -> dict:
    """
    Envía un email HTML usando la configuración SMTP almacenada en DB.
    
    Lee la configuración SMTP desde el modelo Config (smtp_host, smtp_port,
    smtp_email, smtp_password, smtp_use_tls). Soporta TLS mediante STARTTLS.
    Timeout de conexión: 10 segundos.
    
    Args:
        to_email: Dirección de correo destino
        subject: Asunto del email
        html_body: Cuerpo del email en formato HTML
    
    Returns:
        dict con:
            - success (bool): True si se envió correctamente
            - error (str, opcional): Mensaje de error si falló
    
    Esta función NUNCA lanza excepciones. Siempre retorna un dict.
    """
    try:
        cfg = _get_smtp_config()
        
        # Validar configuración mínima
        if not cfg['smtp_host'] or not cfg['smtp_email']:
            return {'success': False, 'error': 'SMTP no configurado'}
        
        smtp_port = int(cfg['smtp_port'])
        use_tls = cfg['smtp_use_tls'].lower() == 'true'
        
        # Construir mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = cfg['smtp_email']
        msg['To'] = to_email
        
        # Adjuntar parte HTML
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(host=cfg['smtp_host'], port=smtp_port, timeout=10)
        
        if use_tls:
            server.starttls()
        
        # Autenticar
        if cfg['smtp_password']:
            server.login(cfg['smtp_email'], cfg['smtp_password'])
        
        # Enviar
        server.send_message(msg)
        server.quit()
        
        return {'success': True}
    
    except Exception as e:
        logging.error(f'Error al enviar email a {to_email}: {str(e)}')
        return {'success': False, 'error': f'Error de conexión SMTP: {str(e)}'}


def render_reset_email(reset_url: str, app_name: str = "Portal de Calificaciones", logo_url: str = "") -> str:
    """
    Genera el template HTML para el email de recuperación de contraseña.
    
    Args:
        reset_url: URL completa con el token JWT para restablecer la contraseña
        app_name: Nombre de la aplicación (personalizable desde Config)
        logo_url: URL absoluta del logo de la universidad (opcional)
    
    Returns:
        String con el HTML completo del email (inline styles para compatibilidad
        con clientes de correo)
    """
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{app_name}" style="max-width: 180px; height: auto; margin-bottom: 20px; display: block;" />'
    else:
        logo_html = f'<h1 style="color: #1a365d; font-size: 24px; font-weight: 700; margin: 0 0 20px 0; text-align: center;">{app_name}</h1>'
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin: 0; padding: 0; background-color: #f4f7fa; font-family: 'Segoe UI', Arial, Helvetica, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f7fa; min-width: 100%;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%); padding: 32px 40px; text-align: center;">
                            {logo_html}
                            <h2 style="color: #ffffff; font-size: 22px; font-weight: 600; margin: 10px 0 0 0;">
                                Recuperación de Contraseña
                            </h2>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #2d3748; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
                                Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en <strong>{app_name}</strong>.
                            </p>
                            
                            <p style="color: #2d3748; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
                                Para continuar, haz clic en el siguiente botón:
                            </p>
                            
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 0 0 32px 0;">
                                        <a href="{reset_url}" 
                                           style="display: inline-block; background: linear-gradient(135deg, #2b6cb0 0%, #2c5282 100%); color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 8px; box-shadow: 0 2px 6px rgba(43,108,176,0.3);">
                                            Restablecer Contraseña
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #718096; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0;">
                                Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:
                            </p>
                            
                            <p style="color: #2b6cb0; font-size: 13px; line-height: 1.5; word-break: break-all; margin: 0 0 24px 0; background: #ebf4ff; padding: 12px; border-radius: 6px;">
                                {reset_url}
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
                            
                            <p style="color: #e53e3e; font-size: 14px; line-height: 1.5; margin: 0 0 8px 0;">
                                <strong>Este enlace expira en 15 minutos.</strong>
                            </p>
                            
                            <p style="color: #718096; font-size: 14px; line-height: 1.5; margin: 0;">
                                Si no solicitaste este cambio, ignora este mensaje. Tu contraseña actual
                                seguirá siendo válida.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #edf2f7; padding: 24px 40px; text-align: center;">
                            <p style="color: #4a5568; font-size: 13px; margin: 0;">
                                &copy; 2026 Universidad Felipe Villanueva &mdash; Todos los derechos reservados
                            </p>
                            <p style="color: #a0aec0; font-size: 12px; margin: 8px 0 0 0;">
                                Este es un mensaje automático, por favor no respondas a este correo.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
