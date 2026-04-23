"""
Rutas para gestión de Materias
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db, Materia, Carrera, Alumno, Calificacion
from utils.decorators import admin_required

materias_bp = Blueprint('materias', __name__)


@materias_bp.route('', methods=['GET'])
def list_materias():
    """
    Lista todas las materias
    Query params:
        - carrera_id: filtrar por carrera
    """
    carrera_id = request.args.get('carrera_id', type=int)
    
    query = Materia.query
    
    if carrera_id:
        query = query.filter(Materia.carrera_id == carrera_id)
    
    materias = query.order_by(Materia.nombre).all()
    
    return jsonify({
        'materias': [m.to_dict() for m in materias]
    }), 200


@materias_bp.route('', methods=['POST'])
@admin_required
def create_materia():
    """
    Crea una nueva materia (admin)
    Body: { nombre, codigo, creditos, carrera_id }
    Al crear una materia, se crean automáticamente registros de calificaciones
    vacías para todos los alumnos de la carrera.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    if not data.get('nombre'):
        return jsonify({'error': 'El nombre es requerido'}), 400
    if not data.get('codigo'):
        return jsonify({'error': 'El código es requerido'}), 400
    if not data.get('carrera_id'):
        return jsonify({'error': 'La carrera es requerida'}), 400
    
    # Verificar que la carrera exista
    carrera = Carrera.query.get(data['carrera_id'])
    if not carrera:
        return jsonify({'error': 'La carrera especificada no existe'}), 404
    
    # Verificar que el código sea único dentro de la carrera
    existing = Materia.query.filter_by(
        carrera_id=data['carrera_id'],
        codigo=data['codigo'].upper()
    ).first()
    if existing:
        return jsonify({'error': 'El código ya existe en esta carrera'}), 409
    
    try:
        # Crear la materia
        materia = Materia(
            nombre=data['nombre'].strip(),
            codigo=data['codigo'].upper().strip(),
            creditos=data.get('creditos', 0),
            carrera_id=data['carrera_id']
        )
        db.session.add(materia)
        db.session.flush()  # Para obtener el ID de la materia
        
        # Obtener el período actual (default)
        periodo_default = data.get('periodo', '2026-1')
        anio_default = data.get('anio', 2026)
        
        # Crear registros de calificaciones vacías para todos los alumnos de la carrera
        alumnos = Alumno.query.filter_by(carrera_id=data['carrera_id'], activo=True).all()
        calificaciones_creadas = 0
        
        for alumno in alumnos:
            # Verificar que no exista ya una calificación para esta materia/período
            existe = Calificacion.query.filter_by(
                alumno_id=alumno.id,
                materia_id=materia.id,
                periodo=periodo_default,
                anio=anio_default
            ).first()
            
            if not existe:
                calificacion = Calificacion(
                    alumno_id=alumno.id,
                    materia_id=materia.id,
                    periodo=periodo_default,
                    anio=anio_default,
                    asistencia_1=0,
                    asistencia_2=0,
                    asistencia_3=0,
                    asistencia_4=0,
                    asistencia_5=0,
                    practica_1=0,
                    practica_2=0,
                    calificacion_final=0
                )
                db.session.add(calificacion)
                calificaciones_creadas += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Materia creada exitosamente',
            'materia': materia.to_dict(),
            'alumnos_notificados': calificaciones_creadas
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear materia: {str(e)}'}), 500


@materias_bp.route('/<int:id>', methods=['GET'])
def get_materia(id):
    """
    Obtiene una materia por ID
    """
    materia = Materia.query.get_or_404(id)
    return jsonify({'materia': materia.to_dict()}), 200


@materias_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_materia(id):
    """
    Actualiza una materia (admin)
    """
    materia = Materia.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    try:
        if 'nombre' in data:
            materia.nombre = data['nombre'].strip()
        if 'codigo' in data:
            new_codigo = data['codigo'].upper().strip()
            if new_codigo != materia.codigo:
                existing = Materia.query.filter_by(
                    carrera_id=materia.carrera_id,
                    codigo=new_codigo
                ).first()
                if existing:
                    return jsonify({'error': 'El código ya está en uso en esta carrera'}), 409
            materia.codigo = new_codigo
        if 'creditos' in data:
            materia.creditos = data['creditos']
        if 'carrera_id' in data:
            new_carrera = Carrera.query.get(data['carrera_id'])
            if not new_carrera:
                return jsonify({'error': 'La carrera especificada no existe'}), 404
            materia.carrera_id = data['carrera_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Materia actualizada exitosamente',
            'materia': materia.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar materia: {str(e)}'}), 500


@materias_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_materia(id):
    """
    Elimina una materia (admin)
    Se eliminan en cascada todas las calificaciones asociadas.
    """
    materia = Materia.query.get_or_404(id)
    
    try:
        # Eliminar todas las calificaciones asociadas (cascada)
        calificaciones_eliminadas = Calificacion.query.filter_by(materia_id=id).delete()
        
        # Eliminar la materia
        db.session.delete(materia)
        db.session.commit()
        
        return jsonify({
            'message': 'Materia eliminada exitosamente',
            'calificaciones_eliminadas': calificaciones_eliminadas
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar materia: {str(e)}'}), 500


@materias_bp.route('/by-carrera/<int:carrera_id>', methods=['GET'])
def get_materias_by_carrera(carrera_id):
    """
    Obtiene todas las materias de una carrera
    """
    carrera = Carrera.query.get_or_404(carrera_id)
    materias = carrera.materias.order_by(Materia.nombre).all()
    
    return jsonify({
        'carrera': carrera.to_dict(),
        'materias': [m.to_dict() for m in materias],
        'total': len(materias)
    }), 200
