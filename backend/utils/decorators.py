"""
Decoradores personalizados para autenticación y autorización
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt


def get_current_user():
    """
    Obtiene el usuario actual basándose en el token JWT
    Retorna un dict con el tipo de usuario (admin/alumno) y sus datos
    """
    from models import Admin, Alumno
    
    verify_jwt_in_request()
    identity = get_jwt_identity()
    
    if identity.get('type') == 'admin':
        return {
            'type': 'admin',
            'data': Admin.query.get(identity['id'])
        }
    elif identity.get('type') == 'alumno':
        return {
            'type': 'alumno',
            'data': Alumno.query.get(identity['id'])
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
            identity = get_jwt_identity()
            
            if identity.get('type') != 'admin':
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de administrador.',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
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
            identity = get_jwt_identity()
            
            if identity.get('type') != 'alumno':
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
            identity = get_jwt_identity()
            
            if identity.get('type') not in ['admin', 'alumno']:
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
    identity = get_jwt_identity()
    
    if identity.get('type') != 'admin':
        return None, jsonify({
            'error': 'Acceso denegado. Se requiere rol de administrador.',
            'code': 'ADMIN_REQUIRED'
        }), 403
    
    admin = Admin.query.get(identity['id'])
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
    identity = get_jwt_identity()
    
    if identity.get('type') != 'alumno':
        return None, jsonify({
            'error': 'Acceso denegado. Se requiere ser alumno.',
            'code': 'ALUMNO_REQUIRED'
        }), 403
    
    alumno = Alumno.query.get(identity['id'])
    if not alumno:
        return None, jsonify({
            'error': 'Alumno no encontrado.',
            'code': 'ALUMNO_NOT_FOUND'
        }), 404
    
    return alumno, None, None
