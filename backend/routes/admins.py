"""
Rutas para gestión de administradores
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Admin
from utils.decorators import admin_required
from utils.security import validate_email

admins_bp = Blueprint('admins', __name__)


@admins_bp.route('/', methods=['GET'])
@admin_required
def list_admins():
    """
    Lista todos los administradores
    """
    admins = Admin.query.all()
    return jsonify({
        'admins': [a.to_dict() for a in admins]
    }), 200


@admins_bp.route('/', methods=['POST'])
@admin_required
def create_admin():
    """
    Crea un nuevo administrador
    Body: { username, email, password, nombre }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    required_fields = ['username', 'email', 'password', 'nombre']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip().lower()
    password = data['password']
    nombre = data['nombre'].strip()
    
    # Validaciones
    if len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Formato de email inválido'}), 400
    
    # Verificar duplicados
    if Admin.query.filter_by(username=username).first():
        return jsonify({'error': 'El nombre de usuario ya existe'}), 409
    
    if Admin.query.filter_by(email=email).first():
        return jsonify({'error': 'El email ya está registrado'}), 409
    
    try:
        admin = Admin(
            username=username,
            email=email,
            nombre=nombre
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Administrador creado exitosamente',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear administrador: {str(e)}'}), 500


@admins_bp.route('/<int:admin_id>', methods=['GET'])
@admin_required
def get_admin(admin_id):
    """
    Obtiene un administrador por ID
    """
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    
    return jsonify({'admin': admin.to_dict()}), 200


@admins_bp.route('/<int:admin_id>', methods=['PUT'])
@admin_required
def update_admin(admin_id):
    """
    Actualiza un administrador
    Body: { username?, email?, nombre? }
    """
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    try:
        # Verificar username único si se está cambiando
        if 'username' in data and data['username'].strip() != admin.username:
            username = data['username'].strip()
            if Admin.query.filter_by(username=username).first():
                return jsonify({'error': 'El nombre de usuario ya existe'}), 409
            admin.username = username
        
        # Verificar email único si se está cambiando
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                return jsonify({'error': 'Formato de email inválido'}), 400
            if Admin.query.filter_by(email=email).first() and email != admin.email:
                return jsonify({'error': 'El email ya está registrado'}), 409
            admin.email = email
        
        if 'nombre' in data:
            admin.nombre = data['nombre'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Administrador actualizado exitosamente',
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar administrador: {str(e)}'}), 500


@admins_bp.route('/<int:admin_id>', methods=['DELETE'])
@admin_required
def delete_admin(admin_id):
    """
    Elimina un administrador (no permite auto-eliminación)
    """
    identity = get_jwt_identity()
    current_admin_id = identity.get('id')
    
    # No permitir auto-eliminación
    if admin_id == current_admin_id:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta'}), 403
    
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    
    # Verificar que queden al menos 2 admins (para no dejar el sistema sin admins)
    total_admins = Admin.query.count()
    if total_admins <= 1:
        return jsonify({'error': 'Debe haber al menos un administrador en el sistema'}), 403
    
    try:
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Administrador eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar administrador: {str(e)}'}), 500


@admins_bp.route('/<int:admin_id>/change-password', methods=['POST'])
@admin_required
def change_admin_password(admin_id):
    """
    Cambia la contraseña de un administrador
    Body: { new_password }
    Solo el propio admin o un admin pueden cambiarla
    """
    identity = get_jwt_identity()
    current_admin_id = identity.get('id')
    
    # Solo el propio admin o cualquier admin puede cambiar la contraseña
    if admin_id != current_admin_id:
        # El usuario actual es admin (por el decorador), así que puede cambiar cualquiera
        pass
    
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    
    data = request.get_json()
    if not data or not data.get('new_password'):
        return jsonify({'error': 'Nueva contraseña requerida'}), 400
    
    new_password = data['new_password']
    if len(new_password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    try:
        admin.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'message': 'Contraseña actualizada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar contraseña: {str(e)}'}), 500
