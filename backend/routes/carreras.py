"""
Rutas para gestión de Carreras
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db, Carrera, Materia
from utils.decorators import admin_required

carreras_bp = Blueprint('carreras', __name__)


@carreras_bp.route('', methods=['GET'])
def list_carreras():
    """
    Lista todas las carreras
    Query params:
        - activa: true/false para filtrar por status
    """
    activa = request.args.get('activa')
    
    query = Carrera.query
    
    if activa is not None:
        query = query.filter(Carrera.activa == (activa.lower() == 'true'))
    
    carreras = query.order_by(Carrera.nombre).all()
    
    return jsonify({
        'carreras': [c.to_dict() for c in carreras]
    }), 200


@carreras_bp.route('', methods=['POST'])
@admin_required
def create_carrera():
    """
    Crea una nueva carrera (admin)
    Body: { nombre, codigo, descripcion, activa }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    if not data.get('nombre'):
        return jsonify({'error': 'El nombre es requerido'}), 400
    if not data.get('codigo'):
        return jsonify({'error': 'El código es requerido'}), 400
    
    # Verificar código único
    if Carrera.query.filter_by(codigo=data['codigo'].upper()).first():
        return jsonify({'error': 'El código ya existe'}), 409
    
    try:
        carrera = Carrera(
            nombre=data['nombre'].strip(),
            codigo=data['codigo'].upper().strip(),
            descripcion=data.get('descripcion', '').strip() or None,
            activa=data.get('activa', True)
        )
        
        db.session.add(carrera)
        db.session.commit()
        
        return jsonify({
            'message': 'Carrera creada exitosamente',
            'carrera': carrera.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear carrera: {str(e)}'}), 500


@carreras_bp.route('/<int:id>', methods=['GET'])
def get_carrera(id):
    """
    Obtiene una carrera por ID
    """
    carrera = Carrera.query.get_or_404(id)
    return jsonify({'carrera': carrera.to_dict()}), 200


@carreras_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_carrera(id):
    """
    Actualiza una carrera (admin)
    """
    carrera = Carrera.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    try:
        if 'nombre' in data:
            carrera.nombre = data['nombre'].strip()
        if 'codigo' in data:
            new_codigo = data['codigo'].upper().strip()
            if new_codigo != carrera.codigo:
                if Carrera.query.filter_by(codigo=new_codigo).first():
                    return jsonify({'error': 'El código ya está en uso'}), 409
            carrera.codigo = new_codigo
        if 'descripcion' in data:
            carrera.descripcion = data['descripcion'].strip() or None
        if 'activa' in data:
            carrera.activa = bool(data['activa'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Carrera actualizada exitosamente',
            'carrera': carrera.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar carrera: {str(e)}'}), 500


@carreras_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_carrera(id):
    """
    Elimina una carrera (admin)
    Solo se permite si no tiene alumnos ni materias asociados
    """
    carrera = Carrera.query.get_or_404(id)
    
    # Verificar que no tenga alumnos
    if carrera.alumnos.count() > 0:
        return jsonify({
            'error': 'No se puede eliminar la carrera porque tiene alumnos asociados'
        }), 400
    
    # Verificar que no tenga materias
    if carrera.materias.count() > 0:
        return jsonify({
            'error': 'No se puede eliminar la carrera porque tiene materias asociadas'
        }), 400
    
    try:
        db.session.delete(carrera)
        db.session.commit()
        
        return jsonify({'message': 'Carrera eliminada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar carrera: {str(e)}'}), 500


@carreras_bp.route('/<int:id>/materias', methods=['GET'])
def get_carrera_materias(id):
    """
    Obtiene las materias de una carrera
    """
    carrera = Carrera.query.get_or_404(id)
    materias = carrera.materias.order_by(Materia.nombre).all()
    
    return jsonify({
        'carrera': carrera.to_dict(),
        'materias': [m.to_dict() for m in materias]
    }), 200


@carreras_bp.route('/<int:id>/alumnos', methods=['GET'])
def get_carrera_alumnos(id):
    """
    Obtiene los alumnos de una carrera
    """
    carrera = Carrera.query.get_or_404(id)
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = carrera.alumnos.order_by(
        db.text('apellido_paterno'), db.text('nombre')
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'carrera': carrera.to_dict(),
        'alumnos': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200
