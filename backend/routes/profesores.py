"""
Rutas para gestión de Profesores
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from models import db, Profesor
from utils.decorators import admin_required

profesores_bp = Blueprint('profesores', __name__)


@profesores_bp.route('', methods=['GET'])
@jwt_required()
def get_profesores():
    """
    Obtiene todos los profesores
    Query params:
        - activo: true/false para filtrar por status
        - page: número de página (default 1)
        - per_page: items por página (default 20)
    """
    activo = request.args.get('activo')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Profesor.query
    
    if activo is not None:
        query = query.filter_by(activo=activo.lower() == 'true')
    
    pagination = query.order_by(Profesor.apellido_paterno).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'profesores': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@profesores_bp.route('/<int:profesor_id>', methods=['GET'])
@jwt_required()
def get_profesor(profesor_id):
    """
    Obtiene un profesor por ID
    """
    profesor = Profesor.query.get_or_404(profesor_id)
    return jsonify({'profesor': profesor.to_dict()}), 200


@profesores_bp.route('', methods=['POST'])
@admin_required
def create_profesor():
    """
    Crea un nuevo profesor
    Body: { numero_empleado, nombre, apellido_paterno, apellido_materno, titulo, email, password }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validar campos requeridos
    required = ['numero_empleado', 'nombre', 'apellido_paterno', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar si ya existe el número de empleado
    if Profesor.query.filter_by(numero_empleado=data['numero_empleado']).first():
        return jsonify({'error': 'El número de empleado ya está registrado'}), 409
    
    # Verificar si ya existe el email
    if Profesor.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'El email ya está registrado'}), 409
    
    profesor = Profesor(
        numero_empleado=data['numero_empleado'],
        nombre=data['nombre'],
        apellido_paterno=data['apellido_paterno'],
        apellido_materno=data.get('apellido_materno'),
        titulo=data.get('titulo'),
        email=data['email'].lower(),
        activo=data.get('activo', True)
    )
    profesor.set_password(data['password'])
    
    db.session.add(profesor)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating profesor: {str(e)}')
        return jsonify({'error': f'Error al crear profesor: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Profesor creado exitosamente',
        'profesor': profesor.to_dict()
    }), 201


@profesores_bp.route('/<int:profesor_id>', methods=['PUT'])
@admin_required
def update_profesor(profesor_id):
    """
    Actualiza un profesor
    Body: { numero_empleado, nombre, apellido_paterno, apellido_materno, titulo, email, password, activo }
    """
    profesor = Profesor.query.get_or_404(profesor_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Actualizar campos
    if 'numero_empleado' in data and data['numero_empleado'] != profesor.numero_empleado:
        if Profesor.query.filter_by(numero_empleado=data['numero_empleado']).first():
            return jsonify({'error': 'El número de empleado ya está registrado'}), 409
        profesor.numero_empleado = data['numero_empleado']
    
    if 'email' in data and data['email'].lower() != profesor.email:
        if Profesor.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        profesor.email = data['email'].lower()
    
    if 'nombre' in data:
        profesor.nombre = data['nombre']
    if 'apellido_paterno' in data:
        profesor.apellido_paterno = data['apellido_paterno']
    if 'apellido_materno' in data:
        profesor.apellido_materno = data['apellido_materno']
    if 'titulo' in data:
        profesor.titulo = data['titulo']
    if 'activo' in data:
        profesor.activo = data['activo']
    if 'password' in data and data['password']:
        profesor.set_password(data['password'])
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating profesor: {str(e)}')
        return jsonify({'error': f'Error al actualizar profesor: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Profesor actualizado exitosamente',
        'profesor': profesor.to_dict()
    }), 200


@profesores_bp.route('/<int:profesor_id>', methods=['DELETE'])
@admin_required
def delete_profesor(profesor_id):
    """
    Elimina o desactiva un profesor
    """
    profesor = Profesor.query.get_or_404(profesor_id)
    
    # Verificar si tiene asignaciones activas
    if profesor.asignaciones.filter_by(activo=True).count() > 0:
        # Desactivar en lugar de eliminar
        profesor.activo = False
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error deactivating profesor: {str(e)}')
            return jsonify({'error': f'Error al desactivar profesor: {str(e)}'}), 500
        return jsonify({
            'message': 'Profesor desactivado (tiene asignaciones activas)',
            'profesor': profesor.to_dict()
        }), 200
    
    db.session.delete(profesor)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting profesor: {str(e)}')
        return jsonify({'error': f'Error al eliminar profesor: {str(e)}'}), 500
    
    return jsonify({'message': 'Profesor eliminado exitosamente'}), 200