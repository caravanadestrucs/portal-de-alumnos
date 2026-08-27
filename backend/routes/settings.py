"""
Blueprint de configuración del sistema (SMTP, personalización, etc.)
Endpoints protegidos para administradores.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt

from models import db, Config
from utils.decorators import admin_required
from utils.email import send_email
from utils.security import validate_email
from extensions import limiter

settings_bp = Blueprint('settings', __name__)


def _validate_smtp_fields(data: dict) -> str | None:
    """
    Valida campos SMTP cuando están presentes en el payload.
    
    Retorna un mensaje de error si hay algún campo inválido,
    o None si todos los campos SMTP son válidos.
    """
    # smtp_host: no vacío
    if 'smtp_host' in data and not data['smtp_host']:
        return 'smtp_host es requerido'
    
    # smtp_port: entero entre 1 y 65535
    if 'smtp_port' in data:
        try:
            port = int(data['smtp_port'])
            if port < 1 or port > 65535:
                return 'smtp_port debe estar entre 1 y 65535'
        except (ValueError, TypeError):
            return 'smtp_port debe ser un número válido'
    
    # smtp_email: formato válido
    if 'smtp_email' in data and data['smtp_email']:
        if not validate_email(data['smtp_email']):
            return 'Formato de email inválido para smtp_email'
    
    # smtp_password: no vacío
    if 'smtp_password' in data and not data['smtp_password']:
        return 'smtp_password es requerido'
    
    # smtp_use_tls: booleano convertible
    if 'smtp_use_tls' in data:
        val = str(data['smtp_use_tls']).lower()
        if val not in ('true', 'false', '1', '0'):
            return 'smtp_use_tls debe ser true o false'
    
    return None


@settings_bp.route('', methods=['GET'])
@admin_required
def get_config():
    """
    GET /api/config
    Obtiene toda la configuración del sistema.
    El smtp_password se retorna enmascarado como "****".
    """
    configs = Config.query.all()
    result = {}
    
    for c in configs:
        if c.key == 'smtp_password' and c.value:
            result[c.key] = '****'
        else:
            result[c.key] = c.value if c.value else ''
    
    return jsonify({'config': result}), 200


@settings_bp.route('', methods=['PUT'])
@limiter.limit("30/hour")
@admin_required
def update_config():
    """
    PUT /api/config
    Actualiza configuración en bulk. Solo actualiza las keys enviadas.
    Las keys no incluidas quedan intactas.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Obtener keys válidas desde la DB
    valid_keys = {c.key for c in Config.query.all()}
    
    # Validar que todas las keys enviadas existan
    unknown_keys = [k for k in data if k not in valid_keys]
    if unknown_keys:
        return jsonify({
            'error': f'Keys desconocidas: {", ".join(unknown_keys)}'
        }), 400
    
    # Validar campos SMTP
    validation_error = _validate_smtp_fields(data)
    if validation_error:
        return jsonify({'error': validation_error}), 400
    
    # Actualizar cada key
    try:
        for key, value in data.items():
            config_entry = Config.query.filter_by(key=key).first()
            if config_entry:
                config_entry.value = str(value) if value is not None else ''
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar configuración: {str(e)}'}), 500
    
    # Retornar configuración actualizada
    configs = Config.query.all()
    result = {}
    for c in configs:
        if c.key == 'smtp_password':
            # Si el password fue incluido en el PUT, devolver el valor real
            # Si no fue incluido, devolver enmascarado
            if 'smtp_password' in data:
                result[c.key] = c.value if c.value else ''
            else:
                result[c.key] = '****' if c.value else ''
        else:
            result[c.key] = c.value if c.value else ''
    
    return jsonify({
        'message': 'Configuración actualizada',
        'config': result
    }), 200


@settings_bp.route('/test', methods=['POST'])
@limiter.limit("10/hour")
@admin_required
def test_email():
    """
    POST /api/config/test
    Envía un email de prueba usando la configuración SMTP actual.
    Si se envía `to_email` en el body, se envía a ese destinatario.
    Si no, se envía al email del administrador autenticado.
    """
    # Obtener email del admin como fallback
    claims = get_jwt()
    from models import Admin
    admin = db.session.get(Admin, claims.get('id'))
    
    # Usar to_email del body si se provee, sino el del admin
    body = request.get_json(silent=True) or {}
    to_email = (body.get('to_email') or '').strip().lower()
    if not to_email:
        if not admin or not admin.email:
            return jsonify({'error': 'Administrador no encontrado o sin email'}), 400
        to_email = admin.email
    
    # Verificar que SMTP esté configurado
    cfg = {c.key: c.value for c in Config.query.all()}
    if not cfg.get('smtp_host') or not cfg.get('smtp_email'):
        return jsonify({
            'error': 'Configuración SMTP incompleta. Configura el servidor SMTP primero.'
        }), 400
    
    # Enviar email de prueba
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #2b6cb0;">Prueba de Configuración SMTP</h2>
    <p>Este es un email de prueba enviado desde <strong>{cfg.get('app_name', 'Portal de Calificaciones')}</strong>.</p>
    <p>Si estás recibiendo este mensaje, la configuración SMTP funciona correctamente.</p>
    <hr />
    <p style="color: #718096; font-size: 12px;">
        Universidad Felipe Villanueva — {cfg.get('app_name', 'Portal de Calificaciones')}
    </p>
</body>
</html>"""
    
    result = send_email(
        to_email=to_email,
        subject=f"Prueba SMTP - {cfg.get('app_name', 'Portal de Calificaciones')}",
        html_body=html
    )
    
    if result.get('success'):
        return jsonify({
            'message': 'Email de prueba enviado exitosamente'
        }), 200
    else:
        return jsonify({
            'error': 'Error al enviar email de prueba',
            'details': result.get('error', 'Error desconocido')
        }), 502
