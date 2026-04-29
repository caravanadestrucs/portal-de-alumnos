"""
Rutas para gestión de Prácticas Profesionales
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from models import db, PracticaProfesional, Alumno

practicas_bp = Blueprint('practicas', __name__)


@practicas_bp.route('', methods=['GET'])
def get_all():
    """Obtiene todas las prácticas profesionales"""
    practicas = PracticaProfesional.query.order_by(PracticaProfesional.alumno_id, PracticaProfesional.numero_practica).all()
    return jsonify([p.to_dict() for p in practicas]), 200


@practicas_bp.route('/alumno/<int:alumno_id>', methods=['GET'])
def get_by_alumno(alumno_id):
    """Obtiene las prácticas de un alumno"""
    practicas = PracticaProfesional.query.filter_by(alumno_id=alumno_id).all()
    return jsonify({
        'practicas': [p.to_dict() for p in practicas],
        'total': len(practicas)
    }), 200


@practicas_bp.route('', methods=['POST'])
def create():
    """Crea una nueva práctica profesional"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    alumno_id = data.get('alumno_id')
    numero_practica = data.get('numero_practica')
    
    if not alumno_id or not numero_practica:
        return jsonify({'error': 'alumno_id y numero_practica son requeridos'}), 400
    
    # Verificar que existe el alumno
    alumno = Alumno.query.get(alumno_id)
    if not alumno:
        return jsonify({'error': 'El alumno no existe'}), 404
    
    # Verificar si ya existe
    existente = PracticaProfesional.query.filter_by(
        alumno_id=alumno_id,
        numero_practica=numero_practica
    ).first()
    
    if existente:
        return jsonify({'error': f'Ya existe una Práctica {numero_practica} para este alumno'}), 400
    
    # Parsear fechas
    fecha_inicio = None
    fecha_fin = None
    if data.get('fecha_inicio'):
        try:
            fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        except:
            pass
    if data.get('fecha_fin'):
        try:
            fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        except:
            pass
    
    practica = PracticaProfesional(
        alumno_id=alumno_id,
        numero_practica=numero_practica,
        nombre_empresa=data.get('nombre_empresa', ''),
        horas=data.get('horas', 480),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=data.get('estado', 'pendiente'),
        observaciones=data.get('observaciones', '')
    )
    
    db.session.add(practica)
    db.session.commit()
    
    return jsonify({
        'message': 'Práctica profesional creada exitosamente',
        'practica': practica.to_dict()
    }), 201


@practicas_bp.route('/<int:practica_id>', methods=['PUT'])
def update(practica_id):
    """Actualiza una práctica profesional"""
    practica = PracticaProfesional.query.get_or_404(practica_id)
    data = request.get_json()
    
    # Actualizar campos
    if 'nombre_empresa' in data:
        practica.nombre_empresa = data['nombre_empresa']
    if 'horas' in data:
        practica.horas = data['horas']
    if 'fecha_inicio' in data:
        if data['fecha_inicio']:
            try:
                practica.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            except:
                pass
        else:
            practica.fecha_inicio = None
    if 'fecha_fin' in data:
        if data['fecha_fin']:
            try:
                practica.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
            except:
                pass
        else:
            practica.fecha_fin = None
    if 'estado' in data:
        practica.estado = data['estado']
    if 'observaciones' in data:
        practica.observaciones = data['observaciones']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Práctica profesional actualizada exitosamente',
        'practica': practica.to_dict()
    }), 200


@practicas_bp.route('/<int:practica_id>', methods=['DELETE'])
def delete(practica_id):
    """Elimina una práctica profesional"""
    practica = PracticaProfesional.query.get_or_404(practica_id)
    
    db.session.delete(practica)
    db.session.commit()
    
    return jsonify({'message': 'Práctica eliminada exitosamente'}), 200