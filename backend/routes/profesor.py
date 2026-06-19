"""
Rutas para que el profesor vea y/edit calificaciones de sus grupos
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime, date

from models import db, Asignacion, GrupoIntegrante, Calificacion

profesor_bp = Blueprint('profesor', __name__)


@profesor_bp.route('/mis-asignaciones', methods=['GET'])
@jwt_required()
def get_mis_asignaciones():
    """Obtiene las asignaciones del profesor actual"""
    claims = get_jwt()
    user_type = claims.get('type')
    user_id = claims.get('id')
    
    profesor_id = request.args.get('profesor_id', type=int)
    
    if not profesor_id:
        return jsonify({'error': 'profesor_id requerido'}), 400
    
    # Solo el mismo profesor o un admin pueden ver
    if user_type != 'admin' and (user_type != 'profesor' or user_id != profesor_id):
        return jsonify({'error': 'No tienes permiso para ver estas asignaciones'}), 403
    
    asignaciones = Asignacion.query.filter_by(profesor_id=profesor_id).all()
    
    return jsonify({
        'asignaciones': [a.to_dict() for a in asignaciones],
        'total': len(asignaciones)
    }), 200


@profesor_bp.route('/asignacion/<int:asignacion_id>/calificaciones', methods=['GET'])
@jwt_required()
def get_calificaciones_asignacion(asignacion_id):
    """Obtiene las calificaciones de los alumnos de una asignacion"""
    claims = get_jwt()
    user_type = claims.get('type')
    user_id = claims.get('id')
    
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    
    # Solo el profesor asignado o un admin pueden ver
    if user_type != 'admin' and (user_type != 'profesor' or user_id != asignacion.profesor_id):
        return jsonify({'error': 'No tienes permiso para ver estas calificaciones'}), 403
    
    integrantes = GrupoIntegrante.query.filter_by(
        grupo_id=asignacion.grupo_id
    ).all()
    
    result = []
    for integ in integrantes:
        calif = Calificacion.query.filter_by(
            alumno_id=integ.alumno_id,
            materia_id=asignacion.materia_id
        ).first()
        
        if calif:
            result.append({
                'alumno': integ.alumno.to_dict_public(),
                'calificacion': calif.to_dict(),
                'puede_editar': asignacion.puede_editar_calificaciones()
            })
        else:
            calif = Calificacion(
                alumno_id=integ.alumno_id,
                materia_id=asignacion.materia_id,
                periodo=f"Enero-Abril {datetime.now().year}",
                anio=datetime.now().year
            )
            db.session.add(calif)
            db.session.flush()
            
            result.append({
                'alumno': integ.alumno.to_dict_public(),
                'calificacion': calif.to_dict(),
                'puede_editar': asignacion.puede_editar_calificaciones()
            })
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error syncing calificaciones: {str(e)}')
        return jsonify({'error': f'Error al obtener calificaciones: {str(e)}'}), 500
    
    return jsonify({
        'asignacion': asignacion.to_dict(),
        'alumnos': result,
        'total': len(result)
    }), 200


@profesor_bp.route('/asignacion/<int:asignacion_id>/calificaciones', methods=['PUT'])
@jwt_required()
def update_calificaciones(asignacion_id):
    """Actualiza las calificaciones de los alumnos de una asignacion"""
    claims = get_jwt()
    user_type = claims.get('type')
    user_id = claims.get('id')
    
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    
    # Solo el profesor asignado o un admin pueden modificar
    if user_type != 'admin' and (user_type != 'profesor' or user_id != asignacion.profesor_id):
        return jsonify({'error': 'No tienes permiso para modificar estas calificaciones'}), 403
    
    if not asignacion.puede_editar_calificaciones():
        return jsonify({'error': 'El período de edición ha terminado'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    alumno_id = data.get('alumno_id')
    calif_data = data.get('calificacion', {})
    
    if not alumno_id:
        return jsonify({'error': 'alumno_id requerido'}), 400
    
    calif = Calificacion.query.filter_by(
        alumno_id=alumno_id,
        materia_id=asignacion.materia_id
    ).first()
    
    if not calif:
        calif = Calificacion(
            alumno_id=alumno_id,
            materia_id=asignacion.materia_id,
            periodo=f"Enero-Abril {datetime.now().year}",
            anio=datetime.now().year
        )
        db.session.add(calif)
    
    for campo in ['asistencia_1', 'asistencia_2', 'asistencia_3', 'asistencia_4', 'asistencia_5',
                 'practica_1', 'practica_2', 'extra_1', 'extra_2', 'calificacion_final']:
        if campo in calif_data:
            valor = calif_data[campo]
            if valor == '' or valor is None:
                setattr(calif, campo, None)
            else:
                setattr(calif, campo, max(0, min(10, float(valor))))
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating calificacion: {str(e)}')
        return jsonify({'error': f'Error al actualizar calificación: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Calificación actualizada',
        'calificacion': calif.to_dict()
    }), 200