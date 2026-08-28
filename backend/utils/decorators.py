"""
Decoradores personalizados para autenticación y autorización
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from models import db


def get_current_user():
    """
    Obtiene el usuario actual basándose en el token JWT
    Retorna un dict con el tipo de usuario (admin/alumno) y sus datos
    """
    from models import Admin, Alumno
    
    verify_jwt_in_request()
    claims = get_jwt()
    
    if (claims.get('user_type') or claims.get('type')) == 'admin':
        return {
            'type': 'admin',
            'data': db.session.get(Admin, claims['id'])
        }
    elif (claims.get('user_type') or claims.get('type')) == 'alumno':
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
            
            if (claims.get('user_type') or claims.get('type')) != 'admin':
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
            
            if (claims.get('user_type') or claims.get('type')) != 'alumno':
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
            
            if (claims.get('user_type') or claims.get('type')) not in ['admin', 'alumno']:
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
    
    if (claims.get('user_type') or claims.get('type')) != 'admin':
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
    
    if (claims.get('user_type') or claims.get('type')) != 'alumno':
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


def general_admin_required(fn):
    """
    Requires role == 'general_admin' (sede_id NULL).
    Returns 403 for sede_admin or non-admin.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if (claims.get('user_type') or claims.get('type')) != 'admin':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de administrador.',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            role = claims.get('role')
            # legacy token without role -> treat as general_admin if no sede_id
            # but strict: if role is missing, deny unless we are migrating; for PR1 we allow legacy as general is not correct
            # Instead check DB role as fallback
            if role is None:
                try:
                    from models import Admin
                    admin = db.session.get(Admin, claims.get('id'))
                    role = getattr(admin, 'role', None) if admin else None
                except Exception:
                    role = None
            if role != 'general_admin':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol general_admin.',
                    'code': 'GENERAL_ADMIN_REQUIRED'
                }), 403
            return fn(*args, **kwargs)
        except Exception as e:
            if e.__class__.__name__ == "RateLimitExceeded" or "RateLimitExceeded" in str(type(e)):
                raise e
            try:
                from flask_limiter.errors import RateLimitExceeded
                if isinstance(e, RateLimitExceeded):
                    raise
            except ImportError:
                pass
            # if already a 403 response, don't swallow
            if hasattr(e, 'code'):
                raise
            return jsonify({
                'error': 'Token inválido o expirado.',
                'code': 'INVALID_TOKEN'
            }), 401
    return wrapper


def sede_scoped_admin_required(fn):
    """
    Allows any admin (general_admin or sede_admin). Blocks alumno/profesor/anon.
    Scoping itself is done via scope_by_sede helper, not here.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if (claims.get('user_type') or claims.get('type')) != 'admin':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de administrador.',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            role = claims.get('role')
            if role not in ('general_admin', 'sede_admin'):
                # fallback: check DB
                try:
                    from models import Admin
                    admin = db.session.get(Admin, claims.get('id'))
                    role = getattr(admin, 'role', None) if admin else None
                except Exception:
                    pass
                if role not in ('general_admin', 'sede_admin'):
                    # legacy without role — allow as admin but log? For PR1 allow
                    # if still not, check type admin passes
                    if (claims.get('user_type') or claims.get('type')) == 'admin':
                        return fn(*args, **kwargs)
                    return jsonify({
                        'error': 'Acceso denegado. Se requiere rol de administrador.',
                        'code': 'ADMIN_REQUIRED'
                    }), 403
            return fn(*args, **kwargs)
        except Exception as e:
            if e.__class__.__name__ == "RateLimitExceeded" or "RateLimitExceeded" in str(type(e)):
                raise e
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
