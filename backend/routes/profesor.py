"""
Rutas para que el profesor vea y/edit calificaciones de sus grupos
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date

from models import db, Asignacion, GrupoIntegrante, Calificacion

profesor_bp = Blueprint('profesor', __name__)


@profesor_bp.route('/mis-asignaciones', methods=['GET'])
def get_mis_asignaciones():
    """Obtiene las asignaciones del profesor actual"""
    profesor_id = request.args.get('profesor_id', type=int)
    
    if not profesor_id:
        return jsonify({'error': 'profesor_id requerido'}), 400
    
    asignaciones = Asignacion.query.filter_by(profesor_id=profesor_id).all()
    
    return jsonify({
        'asignaciones': [a.to_dict() for a in asignaciones],
        'total': len(asignaciones)
    }), 200


@profesor_bp.route('/asignacion/<int:asignacion_id>/calificaciones', methods=['GET'])
def get_calificaciones_asignacion(asignacion_id):
    """Obtiene las calificaciones de los alumnos de una asignacion"""
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    
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
                periodo='Actual',
                anio=datetime.now().year
            )
            db.session.add(calif)
            db.session.flush()
            
            result.append({
                'alumno': integ.alumno.to_dict_public(),
                'calificacion': calif.to_dict(),
                'puede_editar': asignacion.puede_editar_calificaciones()
            })
    
    db.session.commit()
    
    return jsonify({
        'asignacion': asignacion.to_dict(),
        'alumnos': result,
        'total': len(result)
    }), 200


@profesor_bp.route('/asignacion/<int:asignacion_id>/calificaciones', methods=['PUT'])
def update_calificaciones(asignacion_id):
    """Actualiza las calificaciones de los alumnos de una asignacion"""
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    
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
            periodo='Actual',
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
    
    db.session.commit()
    
    return jsonify({
        'message': 'Calificación actualizada',
        'calificacion': calif.to_dict()
    }), 200