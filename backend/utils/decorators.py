"""
Decoradores personalizados para autenticación y autorización
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def get_current_user():
    """
    Obtiene el usuario actual basándose en el token JWT
    Retorna un dict con el tipo de usuario (admin/alumno) y sus datos
    """
    from models import Admin, Alumno
    
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('type') == 'admin':
        return {
            'type': 'admin',
            'data': db.session.get(Admin, claims['id'])
        }
    elif claims.get('type') == 'alumno':
        return {
            'type': 'alumno',
            'data': db.session.get(Alumno, claims['id'])
        }
    
    return None


def admin_required(fn):
    """
    Decorador que requiere que el usuario sea un administrador
    Uso: @admin_required
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('type') != 'admin':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de administrador.',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            # Don't swallow rate limit — let Flask-Limiter return 429
            if e.__class__.__name__ == "RateLimitExceeded" or "RateLimitExceeded" in str(type(e)):
                from flask import current_app
                # Re-raise so limiter's handler can set Retry-After
                raise e
            # Also check via import if available
            try:
                from flask_limiter.errors import RateLimitExceeded
                if isinstance(e, RateLimitExceeded):
                    raise
            except ImportError:
                pass
            return jsonify({
                'error': 'Token inválido o expirado.',
                'code': 'INVALID_TOKEN'
            }), 401
    
    return wrapper


def alumno_required(fn):
    """
    Decorador que requiere que el usuario sea un alumno
    Uso: @alumno_required
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('type') != 'alumno':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere ser alumno.',
                    'code': 'ALUMNO_REQUIRED'
                }), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': 'Token inválido o expirado.',
                'code': 'INVALID_TOKEN'
            }), 401
    
    return wrapper


def login_required(fn):
    """
    Decorador que requiere cualquier usuario autenticado (admin o alumno)
    Uso: @login_required
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('type') not in ['admin', 'alumno']:
                return jsonify({
                    'error': 'Token inválido.',
                    'code': 'INVALID_TOKEN'
                }), 401
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': 'Token inválido o expirado.',
                'code': 'INVALID_TOKEN'
            }), 401
    
    return wrapper


def get_admin_or_403():
    """
    Obtiene el admin actual o retorna error 403
    """
    from models import Admin
    
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('type') != 'admin':
        return None, jsonify({
            'error': 'Acceso denegado. Se requiere rol de administrador.',
            'code': 'ADMIN_REQUIRED'
        }), 403
    
    admin = db.session.get(Admin, claims['id'])
    if not admin:
        return None, jsonify({
            'error': 'Administrador no encontrado.',
            'code': 'ADMIN_NOT_FOUND'
        }), 404
    
    return admin, None, None


def get_alumno_or_403():
    """
    Obtiene el alumno actual o retorna error 403
    """
    from models import Alumno
    
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('type') != 'alumno':
        return None, jsonify({
            'error': 'Acceso denegado. Se requiere ser alumno.',
            'code': 'ALUMNO_REQUIRED'
        }), 403
    
    alumno = db.session.get(Alumno, claims['id'])
    if not alumno:
        return None, jsonify({
            'error': 'Alumno no encontrado.',
            'code': 'ALUMNO_NOT_FOUND'
        }), 404
    
    return alumno, None, None
