"""
Rutas para gestión de Grupos
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Grupo, GrupoIntegrante, Alumno, Carrera
from utils.decorators import admin_required

grupos_bp = Blueprint('grupos', __name__)


@grupos_bp.route('', methods=['GET'])
# @jwt_required()
def get_grupos():
    """
    Obtiene todos los grupos
    """
    carrera_id = request.args.get('carrera_id', type=int)
    activo = request.args.get('activo')
    
    query = Grupo.query
    
    if carrera_id:
        query = query.filter_by(carrera_id=carrera_id)
    if activo is not None:
        query = query.filter_by(activo=activo.lower() == 'true')
    
    grupos = query.order_by(Grupo.nombre).all()
    
    return jsonify({
        'grupos': [g.to_dict() for g in grupos],
        'total': len(grupos)
    }), 200


@grupos_bp.route('/<int:grupo_id>', methods=['GET'])
# @jwt_required()
def get_grupo(grupo_id):
    """
    Obtiene un grupo por ID con sus integrantes
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    
    return jsonify({
        'grupo': grupo.to_dict(),
        'integrantes': [i.to_dict() for i in grupo.integrantes.all()]
    }), 200


@grupos_bp.route('', methods=['POST'])
# @jwt_required()
def create_grupo():
    """
    Crea un nuevo grupo
    Body: { nombre, carrera_id }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    required = ['nombre', 'carrera_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar carrera existe
    carrera = Carrera.query.get(data['carrera_id'])
    if not carrera:
        return jsonify({'error': 'Carrera no encontrada'}), 404
    
    # Verificar que no exista grupo con mismo nombre y carrera
    existing = Grupo.query.filter_by(
        nombre=data['nombre'],
        carrera_id=data['carrera_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Ya existe un grupo con este nombre en la carrera'}), 409
    
    grupo = Grupo(
        nombre=data['nombre'],
        carrera_id=data['carrera_id'],
        activo=data.get('activo', True)
    )
    
    db.session.add(grupo)
    db.session.commit()
    
    return jsonify({
        'message': 'Grupo creado exitosamente',
        'grupo': grupo.to_dict()
    }), 201


@grupos_bp.route('/<int:grupo_id>', methods=['PUT'])
# @jwt_required()
def update_grupo(grupo_id):
    """
    Actualiza un grupo
    Body: { nombre, carrera_id, activo }
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    if 'nombre' in data:
        grupo.nombre = data['nombre']
    if 'carrera_id' in data:
        grupo.carrera_id = data['carrera_id']
    if 'activo' in data:
        grupo.activo = data['activo']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Grupo actualizado exitosamente',
        'grupo': grupo.to_dict()
    }), 200


@grupos_bp.route('/<int:grupo_id>', methods=['DELETE'])
# @jwt_required()
def delete_grupo(grupo_id):
    """
    Elimina un grupo y sus integrantes
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    
    db.session.delete(grupo)
    db.session.commit()
    
    return jsonify({'message': 'Grupo eliminado exitosamente'}), 200


# ============================================================
# INTEGRANTES DEL GRUPO
# ============================================================

@grupos_bp.route('/<int:grupo_id>/integrantes', methods=['GET'])
# @jwt_required()
def get_integrantes(grupo_id):
    """
    Obtiene los integrantes de un grupo
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    
    integrantes = grupo.integrantes.all()
    
    return jsonify({
        'grupo': grupo.to_dict(),
        'integrantes': [i.to_dict() for i in integrantes],
        'total': len(integrantes)
    }), 200


@grupos_bp.route('/<int:grupo_id>/integrantes', methods=['POST'])
# @jwt_required()
def add_integrante(grupo_id):
    """
    Agrega un alumno al grupo
    Body: { alumno_id }
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    data = request.get_json()
    
    if not data or not data.get('alumno_id'):
        return jsonify({'error': 'alumno_id es requerido'}), 400
    
    # Verificar alumno existe
    alumno = Alumno.query.get(data['alumno_id'])
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    # Verificar que no esté ya en el grupo
    existing = GrupoIntegrante.query.filter_by(
        grupo_id=grupo_id,
        alumno_id=data['alumno_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'El alumno ya es parte del grupo'}), 409
    
    integrante = GrupoIntegrante(
        grupo_id=grupo_id,
        alumno_id=data['alumno_id']
    )
    
    db.session.add(integrante)
    db.session.commit()
    
    return jsonify({
        'message': 'Integrante agregado exitosamente',
        'integrante': integrante.to_dict()
    }), 201


@grupos_bp.route('/<int:grupo_id>/integrantes/<int:alumno_id>', methods=['DELETE'])
# @jwt_required()
def remove_integrante(grupo_id, alumno_id):
    """
    Remueve un integrante del grupo
    """
    integrante = GrupoIntegrante.query.filter_by(
        grupo_id=grupo_id,
        alumno_id=alumno_id
    ).first_or_404()
    
    db.session.delete(integrante)
    db.session.commit()
    
    return jsonify({'message': 'Integrante removido exitosamente'}), 200


@grupos_bp.route('/<int:grupo_id>/integrantes/bulk', methods=['POST'])
# @jwt_required()
def add_integrantes_bulk(grupo_id):
    """
    Agrega múltiples alumnos al grupo
    Body: { alumno_ids: [1, 2, 3] }
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    data = request.get_json()
    
    if not data or not data.get('alumno_ids'):
        return jsonify({'error': 'alumno_ids es requerido'}), 400
    
    added = []
    errors = []
    
    for aid in data['alumno_ids']:
        # Verificar que no esté ya en el grupo
        existing = GrupoIntegrante.query.filter_by(
            grupo_id=grupo_id,
            alumno_id=aid
        ).first()
        
        if existing:
            errors.append(f'Alumno {aid} ya está en el grupo')
            continue
        
        integran = GrupoIntegrante(
            grupo_id=grupo_id,
            alumno_id=aid
        )
        db.session.add(integran)
        added.append(aid)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(added)} integrantes agregados',
        'added': added,
        'errors': errors
    }), 201