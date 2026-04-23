"""
Utilidades de seguridad: hashing de contraseñas y JWT
"""
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import bcrypt


def hash_password(password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña
    Bcrypt usa salt rounds = 12 por defecto
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica una contraseña contra su hash bcrypt
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )


def generate_tokens(user_id: int, user_type: str, extra_claims: dict = None):
    """
    Genera access y refresh tokens para un usuario
    
    Args:
        user_id: ID del usuario
        user_type: 'admin' o 'alumno'
        extra_claims: Claims adicionales opcionales
    
    Returns:
        dict con access_token y refresh_token
    """
    identity = {
        'id': user_id,
        'type': user_type
    }
    
    if extra_claims:
        identity.update(extra_claims)
    
    # Token de acceso (24 horas)
    access_token = create_access_token(
        identity=identity,
        expires_delta=timedelta(hours=24)
    )
    
    # Token de refresco (30 días)
    refresh_token = create_refresh_token(
        identity=identity,
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
