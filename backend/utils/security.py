"""
Utilidades de seguridad: hashing de contraseñas y JWT
"""
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
import json


def generate_tokens(user_id: int, user_type: str, extra_claims: dict = None, role: str = None, sede_id: int = None):
    """
    Genera access y refresh tokens para un usuario

    Args:
        user_id: ID del usuario
        user_type: 'admin', 'alumno' o 'profesor'
        extra_claims: Claims adicionales opcionales
        role: admin role ('general_admin'|'sede_admin') — embedded as claim
        sede_id: sede FK — embedded as claim (None for general_admin)

    Returns:
        dict con access_token y refresh_token
    """
    identity = str(user_id)

    # Base user claims (include both type and user_type for compat)
    base_claims = {
        'id': user_id,
        'type': user_type,
        'user_type': user_type,
    }
    if role is not None:
        base_claims['role'] = role
    if sede_id is not None:
        base_claims['sede_id'] = sede_id
    elif role == 'general_admin':
        base_claims['sede_id'] = None
    if extra_claims:
        for k, v in extra_claims.items():
            if k not in base_claims:
                base_claims[k] = v
            elif k in ('role', 'sede_id') and base_claims.get(k) is None:
                base_claims[k] = v

    # Access token can safely overwrite `type` (user type) — access check is lenient
    access_claims = dict(base_claims)
    # Refresh token MUST preserve `type` == "refresh" for jwt_required(refresh=True)
    # so we strip `type` from refresh claims and rely on `user_type`
    refresh_claims = {k: v for k, v in base_claims.items() if k != 'type'}
    # ensure user_type present for refresh
    if 'user_type' not in refresh_claims:
        refresh_claims['user_type'] = user_type
    
    # Token de acceso (24 horas)
    access_token = create_access_token(
        identity=identity,
        additional_claims=access_claims,
        expires_delta=timedelta(hours=24)
    )
    
    # Token de refresco (30 días)
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=refresh_claims,
        expires_delta=timedelta(days=30)
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 86400  # 24 horas en segundos
    }


def validate_email(email: str) -> bool:
    """
    Validación básica de formato de email
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_numero_control(numero_control: str) -> bool:
    """
    Valida formato de número de control
    Formato esperado: 8 dígitos
    """
    import re
    pattern = r'^\d{8}$'
    return re.match(pattern, numero_control) is not None


# ============================================================
# RESET TOKEN (Password Recovery)
# ============================================================

def generate_reset_token(email: str, role: str) -> str:
    """
    Genera un JWT de un solo propósito para restablecimiento de contraseña.
    
    Crea un token JWT con expiración de 15 minutos que contiene los claims
    necesarios para identificar al usuario durante el flujo de recuperación.
    
    Args:
        email: Email del usuario que solicita el reset
        role: Rol del usuario ('admin', 'profesor', 'alumno')
    
    Returns:
        String con el JWT firmado
    
    El token incluye los claims:
        - purpose: 'password_reset' (para diferenciar de access tokens)
        - email: el email del usuario
        - role: el rol del usuario
    """
    token = create_access_token(
        identity=email,
        additional_claims={
            'purpose': 'password_reset',
            'email': email,
            'role': role,
        },
        expires_delta=timedelta(minutes=15)
    )
    return token


def verify_reset_token(token: str) -> dict | None:
    """
    Verifica un reset token JWT.
    
    Decodifica y valida el token, verifica que tenga el propósito correcto
    ('password_reset') y retorna los datos del usuario.
    
    Args:
        token: El token JWT a verificar
    
    Returns:
        dict con { 'email': str, 'role': str } si el token es válido,
        None si el token es inválido, expiró, o no es un reset token
    
    Maneja cualquier excepción de decodificación (firma inválida,
    token expirado, malformado) retornando None.
    """
    from flask import current_app
    
    try:
        decoded = decode_token(token)
        
        if decoded.get('purpose') != 'password_reset':
            return None
        
        email = decoded.get('email')
        role = decoded.get('role')
        
        if not email or not role:
            return None
        
        return {
            'email': email,
            'role': role,
        }
    except Exception:
        return None
