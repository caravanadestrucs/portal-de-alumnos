"""
Rutas de autenticación: login, logout, register, me
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta

from models import db, Admin, Alumno, Profesor
from utils.security import generate_tokens, validate_email, validate_numero_control
from utils.decorators import admin_required, alumno_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Inicio de sesión para admin o alumno
    Body: { email, password }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400
    
    # Buscar en admins
    admin = Admin.query.filter_by(email=email).first()
    if admin and admin.check_password(password):
        tokens = generate_tokens(admin.id, 'admin')
        return jsonify({
            'message': 'Login exitoso',
            'user': {
                'type': 'admin',
                'id': admin.id,
                'username': admin.username,
                'nombre': admin.nombre,
                'email': admin.email
            },
            **tokens
        }), 200
    
    # Buscar en profesores
    profesor = Profesor.query.filter_by(email=email).first()
    if profesor and profesor.check_password(password):
        if not profesor.activo:
            return jsonify({'error': 'Tu cuenta está desactivada. Contacta al administrador.'}), 403
        
        tokens = generate_tokens(profesor.id, 'profesor')
        return jsonify({
            'message': 'Login exitoso',
            'user': {
                'type': 'profesor',
                'id': profesor.id,
                'numero_empleado': profesor.numero_empleado,
                'nombre': f'{profesor.nombre} {profesor.apellido_paterno}',
                'email': profesor.email,
                'titulo': profesor.titulo or '',
            },
            **tokens
        }), 200
    
    # Buscar en alumnos
    alumno = Alumno.query.filter_by(email=email).first()
    if alumno and alumno.check_password(password):
        if not alumno.activo:
            return jsonify({'error': 'Tu cuenta está desactivada. Contacta al administrador.'}), 403
        
        tokens = generate_tokens(alumno.id, 'alumno')
        return jsonify({
            'message': 'Login exitoso',
            'user': {
                'type': 'alumno',
                'id': alumno.id,
                'numero_control': alumno.numero_control,
                'nombre': alumno.nombre_completo,
                'email': alumno.email,
                'carrera': alumno.carrera.nombre if alumno.carrera else None
            },
            **tokens
        }), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registro de nuevo alumno (usado desde /signup del frontend)
    Body: {
        numero_control, nombre, apellido_paterno, apellido_materno,
        email, password, carrera_id
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    required_fields = ['numero_control', 'nombre', 'apellido_paterno', 'email', 'password', 'carrera_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Validar formato número de control
    if not validate_numero_control(data['numero_control']):
        return jsonify({'error': 'El número de control debe tener 8 dígitos'}), 400
    
    # Validar email
    if not validate_email(data['email']):
        return jsonify({'error': 'Formato de email inválido'}), 400
    
    # Verificar que no exista el número de control
    if Alumno.query.filter_by(numero_control=data['numero_control']).first():
        return jsonify({'error': 'El número de control ya está registrado'}), 409
    
    # Verificar que no exista el email
    if Alumno.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'El email ya está registrado'}), 409
    
    # Crear alumno
    try:
        alumno = Alumno(
            numero_control=data['numero_control'],
            nombre=data['nombre'].strip(),
            apellido_paterno=data['apellido_paterno'].strip(),
            apellido_materno=data.get('apellido_materno', '').strip() or None,
            email=data['email'].lower().strip(),
            carrera_id=data['carrera_id'],
            activo=True,
            fecha_registro=datetime.utcnow().date()
        )
        alumno.set_password(data['password'])
        
        db.session.add(alumno)
        db.session.commit()
        
        # Generar tokens para login automático
        tokens = generate_tokens(alumno.id, 'alumno')
        
        return jsonify({
            'message': 'Registro exitoso',
            'user': {
                'type': 'alumno',
                'id': alumno.id,
                'numero_control': alumno.numero_control,
                'nombre': alumno.nombre_completo,
                'email': alumno.email
            },
            **tokens
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cerrar sesión (el token se invalida desde el cliente)
    """
    # En una implementación completa, agregaríamos el token a una blacklist
    # Por ahora, simplemente retornamos éxito
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtiene la información del usuario actual
    """
    identity = get_jwt_identity()
    user_type = identity.get('type')
    user_id = identity.get('id')
    
    if user_type == 'admin':
        admin = Admin.query.get(user_id)
        if not admin:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        return jsonify({
            'type': 'admin',
            'user': admin.to_dict()
        }), 200
    
    elif user_type == 'alumno':
        alumno = Alumno.query.get(user_id)
        if not alumno:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        return jsonify({
            'type': 'alumno',
            'user': alumno.to_dict_public()
        }), 200
    
    return jsonify({'error': 'Tipo de usuario inválido'}), 400


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Refresca el token de acceso usando el refresh token
    """
    identity = get_jwt_identity()
    tokens = generate_tokens(identity['id'], identity['type'])
    
    return jsonify({
        'message': 'Token refrescado',
        **tokens
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Cambiar contraseña del usuario actual
    Body: { current_password, new_password }
    """
    identity = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Contraseña actual y nueva son requeridas'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    user_type = identity.get('type')
    user_id = identity.get('id')
    
    try:
        if user_type == 'admin':
            user = Admin.query.get(user_id)
            if not user.check_password(current_password):
                return jsonify({'error': 'Contraseña actual incorrecta'}), 401
            user.set_password(new_password)
        else:
            user = Alumno.query.get(user_id)
            if not user.check_password(current_password):
                return jsonify({'error': 'Contraseña actual incorrecta'}), 401
            user.set_password(new_password)
        
        db.session.commit()
        return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500
