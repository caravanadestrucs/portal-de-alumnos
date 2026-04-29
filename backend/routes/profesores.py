"""
Rutas para gestión de Profesores
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Profesor
from utils.decorators import admin_required

profesores_bp = Blueprint('profesores', __name__)


@profesores_bp.route('', methods=['GET'])
# @jwt_required()
def get_profesores():
    """
    Obtiene todos los profesores
    """
    activo = request.args.get('activo')
    
    query = Profesor.query
    
    if activo is not None:
        query = query.filter_by(activo=activo.lower() == 'true')
    
    profesores = query.order_by(Profesor.apellido_paterno).all()
    
    return jsonify({
        'profesores': [p.to_dict() for p in profesores],
        'total': len(profesores)
    }), 200


@profesores_bp.route('/<int:profesor_id>', methods=['GET'])
# @jwt_required()
def get_profesor(profesor_id):
    """
    Obtiene un profesor por ID
    """
    profesor = Profesor.query.get_or_404(profesor_id)
    return jsonify({'profesor': profesor.to_dict()}), 200


@profesores_bp.route('', methods=['POST'])
# @jwt_required()
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
    db.session.commit()
    
    return jsonify({
        'message': 'Profesor creado exitosamente',
        'profesor': profesor.to_dict()
    }), 201


@profesores_bp.route('/<int:profesor_id>', methods=['PUT'])
# @jwt_required()
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
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profesor actualizado exitosamente',
        'profesor': profesor.to_dict()
    }), 200


@profesores_bp.route('/<int:profesor_id>', methods=['DELETE'])
# @jwt_required()
def delete_profesor(profesor_id):
    """
    Elimina o desactiva un profesor
    """
    profesor = Profesor.query.get_or_404(profesor_id)
    
    # Verificar si tiene asignaciones activas
    if profesor.asignaciones.filter_by(activo=True).count() > 0:
        # Desactivar en lugar de eliminar
        profesor.activo = False
        db.session.commit()
        return jsonify({
            'message': 'Profesor desactivado (tiene asignaciones activas)',
            'profesor': profesor.to_dict()
        }), 200
    
    db.session.delete(profesor)
    db.session.commit()
    
    return jsonify({'message': 'Profesor eliminado exitosamente'}), 200