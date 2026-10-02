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


from functools import wraps as _wraps
from flask import jsonify as _jsonify, g as _g, request as _request
from flask_jwt_extended import verify_jwt_in_request as _verify, get_jwt as _get_jwt

def forbidden_uniform():
    return _jsonify({'error': 'Forbidden', 'code': 'CROSS_SEDE'}), 403

def has_global_scope(claims):
    """True when claims carry global (cross-sede) scope: general roles, or a
    legacy admin token without role (same taxonomy as require_sede)."""
    role = (claims or {}).get('role')
    if role in ('general_admin', 'general'):
        return True
    if ((claims or {}).get('user_type') or (claims or {}).get('type')) == 'admin' and role is None:
        return True
    return False


def uniform_missing_response(claims):
    """Detail anti-enumeration for missing resources: return None when the
    caller has global scope (caller then returns its real 404), otherwise
    return uniform 403 so ids cannot be probed across sedes."""
    if has_global_scope(claims):
        return None
    return forbidden_uniform()

def public_route(fn):
    fn._portal_scope = 'public'
    return fn

def global_route(fn):
    fn._portal_scope = 'global'
    return fn

def require_sede(_fn=None, *, resolve="body_sede_id"):
    def deco(fn):
        @_wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                _verify()
            except Exception:
                return _jsonify({'error': 'Token inválido o expirado.', 'code': 'INVALID_TOKEN'}), 401
            claims = _get_jwt()
            role = claims.get('role')
            token_sede = claims.get('sede_id')
            user_type = claims.get('user_type') or claims.get('type')
            # Resolver sede objetivo: body ? query ? join la resuelve el handler vía g
            target = None
            try:
                body = _request.get_json(silent=True) or {}
                if isinstance(body, dict) and body.get('sede_id') is not None:
                    target = int(body.get('sede_id'))
            except Exception:
                target = None
            if target is None:
                qs = _request.args.get('sede_id', type=int)
                if qs is not None:
                    if role not in ('general_admin', 'general') and (user_type != 'admin' or role is None):
                        # rol no-general enviando ?sede_id → 403 e ignorar para scope
                        if role in ('sede_admin',) or user_type in ('profesor', 'alumno'):
                            return forbidden_uniform()
                    if role in ('general_admin', 'general') or (user_type == 'admin' and role is None):
                        target = qs
            # Autorizar
            if role == 'sede_admin':
                if token_sede is None:
                    return forbidden_uniform()
                if target is not None and int(target) != int(token_sede):
                    return forbidden_uniform()
                _g.scoped_sede_id = token_sede
            elif role in ('general_admin', 'general') or (user_type == 'admin' and role is None):
                _g.scoped_sede_id = target  # None = todas (list) ; write exige sede explícita (Task 5)
                if role in ('general_admin', 'general') and target is not None:
                    try:
                        from models import db as _db, AuditLog as _Audit
                        _db.session.add(_Audit(actor_id=claims.get('id'), actor_role=role,
                            method=_request.method, path=_request.path, target_sede_id=int(target)))
                        _db.session.commit()
                    except Exception:
                        try: _db.session.rollback()
                        except Exception: pass
            elif user_type in ('profesor', 'alumno'):
                _g.scoped_sede_id = token_sede
                if target is not None and token_sede is not None and int(target) != int(token_sede):
                    return forbidden_uniform()
            else:
                return forbidden_uniform()
            fn._portal_scope = 'sede'
            return fn(*args, **kwargs)
        wrapper._portal_scope = 'sede'
        return wrapper
    if _fn is not None:
        return deco(_fn)
    return deco
