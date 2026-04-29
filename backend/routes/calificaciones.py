"""
Rutas para gestión de Calificaciones
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Calificacion, Alumno, Materia
from utils.decorators import admin_required

calificaciones_bp = Blueprint('calificaciones', __name__)


@calificaciones_bp.route('/alumnos/<int:alumno_id>', methods=['GET'])
# @jwt_required()
def get_alumno_calificaciones(alumno_id):
    """
    Obtiene todas las calificaciones de un alumno
    """
    # Por ahora permitir sin JWT para debug
    # identity = get_jwt_identity()
    
    # # Verificar permisos: solo el admin o el propio alumno
    # if identity.get('type') == 'alumno' and identity['id'] != alumno_id:
    #     return jsonify({'error': 'No tienes permiso para ver estas calificaciones'}), 403
    
    alumno = Alumno.query.get_or_404(alumno_id)
    
    # Filtros opcionales
    periodo = request.args.get('periodo')
    anio = request.args.get('anio', type=int)
    materia_id = request.args.get('materia_id', type=int)
    
    query = Calificacion.query.filter_by(alumno_id=alumno_id)
    
    if periodo:
        query = query.filter(Calificacion.periodo == periodo)
    if anio:
        query = query.filter(Calificacion.anio == anio)
    if materia_id:
        query = query.filter(Calificacion.materia_id == materia_id)
    
    calificaciones = query.order_by(Calificacion.anio.desc(), Calificacion.periodo).all()
    
    return jsonify({
        'alumno': alumno.to_dict_public(),
        'calificaciones': [c.to_dict() for c in calificaciones],
        'total': len(calificaciones)
    }), 200


@calificaciones_bp.route('', methods=['POST'])
@admin_required
def create_or_update_calificacion():
    """
    Crea o actualiza una calificación (admin)
    Body: {
        alumno_id, materia_id, asistencia_1-5, practica_1, practica_2,
        calificacion_final, periodo, anio
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    required_fields = ['alumno_id', 'materia_id', 'periodo', 'anio']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar que el alumno exista
    alumno = Alumno.query.get(data['alumno_id'])
    if not alumno:
        return jsonify({'error': 'El alumno no existe'}), 404
    
    # Verificar que la materia exista
    materia = Materia.query.get(data['materia_id'])
    if not materia:
        return jsonify({'error': 'La materia no existe'}), 404
    
    # Buscar calificación existente o crear nueva
    calificacion = Calificacion.query.filter_by(
        alumno_id=data['alumno_id'],
        materia_id=data['materia_id'],
        periodo=data['periodo'],
        anio=data['anio']
    ).first()
    
    try:
        if calificacion:
            # Actualizar existente
            if 'asistencia_1' in data:
                calificacion.asistencia_1 = max(0, min(1, int(data['asistencia_1'])))
            if 'asistencia_2' in data:
                calificacion.asistencia_2 = max(0, min(1, int(data['asistencia_2'])))
            if 'asistencia_3' in data:
                calificacion.asistencia_3 = max(0, min(1, int(data['asistencia_3'])))
            if 'asistencia_4' in data:
                calificacion.asistencia_4 = max(0, min(1, int(data['asistencia_4'])))
            if 'asistencia_5' in data:
                calificacion.asistencia_5 = max(0, min(1, int(data['asistencia_5'])))
            if 'practica_1' in data:
                calificacion.practica_1 = max(0, min(10, float(data['practica_1'])))
            if 'practica_2' in data:
                calificacion.practica_2 = max(0, min(10, float(data['practica_2'])))
            if 'extra_1' in data:
                calificacion.extra_1 = max(0, min(10, float(data['extra_1'])))
            if 'extra_2' in data:
                calificacion.extra_2 = max(0, min(10, float(data['extra_2'])))
            if 'calificacion_final' in data:
                calificacion.calificacion_final = max(0, min(10, float(data['calificacion_final'])))
            
            message = 'Calificación actualizada exitosamente'
        else:
            # Crear nueva
            calificacion = Calificacion(
                alumno_id=data['alumno_id'],
                materia_id=data['materia_id'],
                asistencia_1=max(0, min(1, int(data.get('asistencia_1', 0)))),
                asistencia_2=max(0, min(1, int(data.get('asistencia_2', 0)))),
                asistencia_3=max(0, min(1, int(data.get('asistencia_3', 0)))),
                asistencia_4=max(0, min(1, int(data.get('asistencia_4', 0)))),
                asistencia_5=max(0, min(1, int(data.get('asistencia_5', 0)))),
                practica_1=max(0, min(10, float(data.get('practica_1', 0)))),
                practica_2=max(0, min(10, float(data.get('practica_2', 0)))),
                extra_1=max(0, min(10, float(data.get('extra_1', 0)))),
                extra_2=max(0, min(10, float(data.get('extra_2', 0)))),
                calificacion_final=max(0, min(10, float(data.get('calificacion_final', 0)))),
                periodo=data['periodo'],
                anio=data['anio']
            )
            db.session.add(calificacion)
            message = 'Calificación creada exitosamente'
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'calificacion': calificacion.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar calificación: {str(e)}'}), 500


@calificaciones_bp.route('/alumnos/<int:alumno_id>/historial', methods=['GET'])
@jwt_required()
def get_historial(alumno_id):
    """
    Obtiene el historial completo del alumno (para el portal)
    Incluye calificaciones, promedio general, etc.
    """
    identity = get_jwt_identity()
    
    # Verificar permisos
    if identity.get('type') == 'alumno' and identity['id'] != alumno_id:
        return jsonify({'error': 'No tienes permiso para ver este historial'}), 403
    
    alumno = Alumno.query.get_or_404(alumno_id)
    
    # Obtener todas las calificaciones
    calificaciones = Calificacion.query.filter_by(alumno_id=alumno_id)\
        .order_by(Calificacion.anio.desc(), Calificacion.periodo.desc()).all()
    
    # Calcular estadísticas
    total_calificaciones = len(calificaciones)
    materias_aprobadas = sum(1 for c in calificaciones if c.calificacion_final >= 13)
    materias_reprobadas = sum(1 for c in calificaciones if c.calificacion_final > 0 and c.calificacion_final < 13)
    
    promedios = [c.calificacion_final for c in calificaciones if c.calificacion_final > 0]
    promedio_general = round(sum(promedios) / len(promedios), 1) if promedios else 0
    
    # Agrupar por periodo/año
    historial = {}
    for cal in calificaciones:
        key = f"{cal.periodo} {cal.anio}"
        if key not in historial:
            historial[key] = {
                'periodo': cal.periodo,
                'anio': cal.anio,
                'materias': []
            }
        historial[key]['materias'].append(cal.to_dict())
    
    return jsonify({
        'alumno': alumno.to_dict_public(),
        'promedio_general': promedio_general,
        'estadisticas': {
            'total_materias': total_calificaciones,
            'aprobadas': materias_aprobadas,
            'reprobadas': materias_reprobadas,
            'en_curso': total_calificaciones - materias_aprobadas - materias_reprobadas
        },
        'historial': list(historial.values())
    }), 200


@calificaciones_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_calificacion(id):
    """
    Obtiene una calificación por ID
    """
    calificacion = Calificacion.query.get_or_404(id)
    
    identity = get_jwt_identity()
    if identity.get('type') == 'alumno' and identity['id'] != calificacion.alumno_id:
        return jsonify({'error': 'No tienes permiso para ver esta calificación'}), 403
    
    return jsonify({'calificacion': calificacion.to_dict()}), 200


@calificaciones_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_calificacion(id):
    """
    Elimina una calificación (admin)
    """
    calificacion = Calificacion.query.get_or_404(id)
    
    try:
        db.session.delete(calificacion)
        db.session.commit()
        
        return jsonify({'message': 'Calificación eliminada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar calificación: {str(e)}'}), 500


@calificaciones_bp.route('/periodos', methods=['GET'])
def get_periodos():
    """
    Obtiene todos los periodos/años únicos en las calificaciones
    """
    from sqlalchemy import func, distinct
    
    resultados = db.session.query(
        distinct(Calificacion.periodo),
        distinct(Calificacion.anio)
    ).order_by(Calificacion.anio.desc()).all()
    
    periodos = []
    seen = set()
    for periodo, anio in resultados:
        key = f"{periodo} {anio}"
        if key not in seen:
            seen.add(key)
            periodos.append({
                'periodo': periodo,
                'anio': anio,
                'label': f"{periodo} {anio}"
            })
    
    return jsonify({'periodos': periodos}), 200


@calificaciones_bp.route('/bulk', methods=['POST'])
@admin_required
def bulk_create_calificaciones():
    """
    Crea múltiples calificaciones a la vez (admin)
    Body: { calificaciones: [...] }
    """
    data = request.get_json()
    
    if not data or not data.get('calificaciones'):
        return jsonify({'error': 'Se requiere un array de calificaciones'}), 400
    
    created = []
    errors = []
    
    for i, cal_data in enumerate(data['calificaciones']):
        try:
            # Validaciones básicas
            if not cal_data.get('alumno_id') or not cal_data.get('materia_id'):
                errors.append(f"Fila {i}: alumno_id y materia_id son requeridos")
                continue
            
            # Verificar existencia
            alumno = Alumno.query.get(cal_data['alumno_id'])
            materia = Materia.query.get(cal_data['materia_id'])
            
            if not alumno or not materia:
                errors.append(f"Fila {i}: Alumno o materia no encontrada")
                continue
            
            # Buscar existente
            existente = Calificacion.query.filter_by(
                alumno_id=cal_data['alumno_id'],
                materia_id=cal_data['materia_id'],
                periodo=cal_data.get('periodo', 'Regular'),
                anio=cal_data.get('anio', 2026)
            ).first()
            
            if existente:
                existente.calificacion_final = max(0, min(10, float(cal_data.get('calificacion_final', 0))))
                existente.practica_1 = max(0, min(10, float(cal_data.get('practica_1', 0))))
                existente.practica_2 = max(0, min(10, float(cal_data.get('practica_2', 0))))
                existente.extra_1 = max(0, min(10, float(cal_data.get('extra_1', 0))))
                existente.extra_2 = max(0, min(10, float(cal_data.get('extra_2', 0))))
            else:
                nueva = Calificacion(
                    alumno_id=cal_data['alumno_id'],
                    materia_id=cal_data['materia_id'],
                    practica_1=max(0, min(10, float(cal_data.get('practica_1', 0)))),
                    practica_2=max(0, min(10, float(cal_data.get('practica_2', 0)))),
                    extra_1=max(0, min(10, float(cal_data.get('extra_1', 0)))),
                    extra_2=max(0, min(10, float(cal_data.get('extra_2', 0)))),
                    calificacion_final=max(0, min(10, float(cal_data.get('calificacion_final', 0)))),
                    periodo=cal_data.get('periodo', 'Regular'),
                    anio=cal_data.get('anio', 2026)
                )
                db.session.add(nueva)
            
            created.append(i)
            
        except Exception as e:
            errors.append(f"Fila {i}: {str(e)}")
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'{len(created)} calificaciones procesadas',
            'created': len(created),
            'errors': errors
        }), 200 if not errors else 207
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar: {str(e)}'}), 500
