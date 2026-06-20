"""
Rutas de autenticación: login, logout, register, me, forgot-password, reset-password
"""
import os
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt
)
from datetime import datetime, timedelta

from models import db, Admin, Alumno, Profesor, Carrera, Materia, Calificacion, Config
from utils.security import generate_tokens, validate_email, validate_numero_control, generate_reset_token, verify_reset_token
from utils.decorators import admin_required, alumno_required
from utils.email import send_email, render_reset_email
from extensions import limiter

auth_bp = Blueprint('auth', __name__)


# ============================================================
# HELPERS
# ============================================================

def _find_user_by_email(email: str) -> tuple:
    """
    Busca un usuario por email secuencialmente en las 3 tablas.
    
    El orden de búsqueda es: Admin → Profesor → Alumno.
    
    Args:
        email: Dirección de email a buscar
    
    Returns:
        tuple (user, role_string):
            - (Admin, 'admin') si se encuentra en admins
            - (Profesor, 'profesor') si se encuentra en profesores
            - (Alumno, 'alumno') si se encuentra en alumnos
            - (None, None) si no se encuentra en ninguna tabla
    """
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        return admin, 'admin'
    
    profesor = Profesor.query.filter_by(email=email).first()
    if profesor:
        return profesor, 'profesor'
    
    alumno = Alumno.query.filter_by(email=email).first()
    if alumno:
        return alumno, 'alumno'
    
    return None, None


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@limiter.limit("10/minute")
def login():
    """
    Inicio de sesión para admin o alumno
    Body: { email, password }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
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
        db.session.flush()  # Obtener ID del alumno
        
        # Crear boletas para todas las materias de su carrera
        materias = Materia.query.filter_by(carrera_id=data['carrera_id']).all()
        periodo_actual = f"Enero-Abril {datetime.now().year}"
        for materia in materias:
            calif = Calificacion(
                alumno_id=alumno.id,
                materia_id=materia.id,
                periodo=periodo_actual,
                anio=datetime.now().year
            )
            db.session.add(calif)
        
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
    claims = get_jwt()
    user_type = claims.get('type')
    user_id = claims.get('id')
    
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
    claims = get_jwt()
    tokens = generate_tokens(claims['id'], claims['type'])
    
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
    claims = get_jwt()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Contraseña actual y nueva son requeridas'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    user_type = claims.get('type')
    user_id = claims.get('id')
    
    try:
        if user_type == 'admin':
            user = Admin.query.get(user_id)
            if not user or not user.check_password(current_password):
                return jsonify({'error': 'Contraseña actual incorrecta'}), 401
            user.set_password(new_password)
        elif user_type == 'profesor':
            user = Profesor.query.get(user_id)
            if not user or not user.check_password(current_password):
                return jsonify({'error': 'Contraseña actual incorrecta'}), 401
            user.set_password(new_password)
        else:
            user = Alumno.query.get(user_id)
            if not user or not user.check_password(current_password):
                return jsonify({'error': 'Contraseña actual incorrecta'}), 401
            user.set_password(new_password)
        
        db.session.commit()
        return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500


# ============================================================
# PASSWORD RECOVERY
# ============================================================

@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5/hour")
def forgot_password():
    """
    POST /api/auth/forgot-password
    Solicitar recuperación de contraseña.
    
    Body: { "email": "user@example.com" }
    
    SIEMPRE retorna 200 independientemente de si el email existe o no,
    para no revelar qué emails están registrados (seguridad por obscuridad).
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'El email es requerido'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Formato de email inválido'}), 400
    
    # Buscar usuario en las 3 tablas
    user, role = _find_user_by_email(email)
    
    if user and role:
        try:
            # Generar token JWT de 15 minutos
            token = generate_reset_token(email, role)
            
            # Construir URL de reset
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
            reset_url = f"{frontend_url}/reset-password?token={token}"
            
            # Leer configuración de personalización para el template
            app_configs = {c.key: c.value for c in Config.query.all()}
            app_name = app_configs.get('app_name', 'Portal de Calificaciones')
            logo_url = app_configs.get('app_logo_url', '')
            
            # Renderizar template y enviar email
            html_body = render_reset_email(reset_url, app_name=app_name, logo_url=logo_url)
            result = send_email(email, "Recuperación de Contraseña", html_body)
            
            if result.get('success'):
                print(f'[EMAIL] Link de recuperación enviado a {email}')
            else:
                print(f'[EMAIL] Error al enviar a {email}: {result.get("error")}')
                
        except Exception as e:
            # Error al generar token o enviar email — loggear pero responder 200
            print(f'[EMAIL] Error en forgot-password para {email}: {str(e)}')
    else:
        # Email no registrado: loggear pero responder igual
        print(f'[EMAIL] Solicitud de recuperación para email no registrado: {email}')
        # Pequeño sleep para mitigar timing attacks
        time.sleep(0.1)
    
    # SIEMPRE retornar 200 con el mismo mensaje
    return jsonify({
        'message': 'Si el email está registrado, recibirás un enlace de recuperación en tu bandeja de entrada'
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("10/hour")
def reset_password():
    """
    POST /api/auth/reset-password
    Restablecer contraseña usando token JWT.
    
    Body: { "token": "<jwt>", "password": "nueva-contraseña" }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    token = data.get('token')
    password = data.get('password')
    
    if not token:
        return jsonify({'error': 'Token requerido'}), 400
    
    if not password:
        return jsonify({'error': 'La contraseña es requerida'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    # Verificar token JWT
    token_data = verify_reset_token(token)
    if not token_data:
        return jsonify({'error': 'Token inválido o expirado'}), 400
    
    email = token_data.get('email')
    role = token_data.get('role')
    
    # Buscar usuario según el rol del token
    try:
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
        elif role == 'profesor':
            user = Profesor.query.filter_by(email=email).first()
        elif role == 'alumno':
            user = Alumno.query.filter_by(email=email).first()
        else:
            return jsonify({'error': 'Rol de usuario inválido'}), 400
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 400
        
        # Actualizar contraseña
        user.set_password(password)
        db.session.commit()
        
        return jsonify({'message': 'Contraseña actualizada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al restablecer contraseña: {str(e)}'}), 500
