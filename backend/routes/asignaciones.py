"""
Rutas para gestión de Asignaciones
(profesor → materia → grupo → fechas)
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime

from models import db, Asignacion, Profesor, Materia, Grupo
from utils.decorators import admin_required

asignaciones_bp = Blueprint('asignaciones', __name__)


@asignaciones_bp.route('', methods=['GET'])
@jwt_required()
def get_asignaciones():
    """
    Obtiene todas las asignaciones
    Query params:
        - profesor_id: filtrar por profesor
        - materia_id: filtrar por materia
        - grupo_id: filtrar por grupo
        - activo: true/false para filtrar por status
        - page: número de página (default 1)
        - per_page: items por página (default 20)
    """
    profesor_id = request.args.get('profesor_id', type=int)
    materia_id = request.args.get('materia_id', type=int)
    grupo_id = request.args.get('grupo_id', type=int)
    activo = request.args.get('activo')
    page = request.args.get('page', 1, type=int)
    try:
        per_page = max(1, min(int(request.args.get('per_page', 20)), 100))
    except ValueError:
        per_page = 20
    
    query = Asignacion.query.join(Grupo, Asignacion.grupo_id == Grupo.id)
    # sede scoping: sede_admin only sees asignaciones where grupo.sede_id == token.sede
    claims = get_jwt()
    if claims.get('role') == 'sede_admin':
        token_sede = claims.get('sede_id')
        query = query.filter(Grupo.sede_id == token_sede)
    else:
        # general_admin optional ?sede_id filter
        qs_sede = request.args.get('sede_id', type=int)
        if qs_sede is not None:
            query = query.filter(Grupo.sede_id == qs_sede)
    
    if profesor_id:
        query = query.filter(Asignacion.profesor_id == profesor_id)
    if materia_id:
        query = query.filter(Asignacion.materia_id == materia_id)
    if grupo_id:
        query = query.filter(Asignacion.grupo_id == grupo_id)
    if activo is not None:
        query = query.filter(Asignacion.activo == (activo.lower() == 'true'))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'asignaciones': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


def _asig_forbidden(asignacion):
    claims = get_jwt()
    if claims.get('role') != 'sede_admin':
        return False
    token_sede = claims.get('sede_id')
    grupo = db.session.get(Grupo, asignacion.grupo_id)
    if grupo and grupo.sede_id != token_sede:
        return True
    # also check profesor sede if exists
    prof = db.session.get(Profesor, asignacion.profesor_id)
    if prof and prof.sede_id and prof.sede_id != token_sede:
        return True
    return False


@asignaciones_bp.route('/<int:asignacion_id>', methods=['GET'])
@jwt_required()
def get_asignacion(asignacion_id):
    """
    Obtiene una asignacion por ID — scoped
    """
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    if _asig_forbidden(asignacion):
        return jsonify({'error': 'Cross-sede forbidden', 'code': 'CROSS_SEDE'}), 403
    return jsonify({'asignacion': asignacion.to_dict()}), 200


@asignaciones_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_asignacion():
    """
    Crea una nueva asignacion
    Body: { profesor_id, materia_id, grupo_id, fecha_inicio, fecha_fin }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    required = ['profesor_id', 'materia_id', 'grupo_id', 'fecha_inicio', 'fecha_fin']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar que existe el profesor
    profesor = db.session.get(Profesor, data['profesor_id'])
    if not profesor:
        return jsonify({'error': 'Profesor no encontrado'}), 404
    
    # Verificar que existe la materia
    materia = db.session.get(Materia, data['materia_id'])
    if not materia:
        return jsonify({'error': 'Materia no encontrada'}), 404
    
    # Verificar que existe el grupo
    grupo = db.session.get(Grupo, data['grupo_id'])
    if not grupo:
        return jsonify({'error': 'Grupo no encontrado'}), 404

    # sede scoping: all must belong to same sede for sede_admin
    claims = get_jwt()
    if claims.get('role') == 'sede_admin':
        token_sede = claims.get('sede_id')
        if grupo.sede_id != token_sede:
            return jsonify({'error': 'Cross-sede grupo forbidden', 'code': 'CROSS_SEDE'}), 403
        if profesor.sede_id and profesor.sede_id != token_sede:
            return jsonify({'error': 'Cross-sede profesor forbidden', 'code': 'CROSS_SEDE'}), 403
    
    # Parsear fechas
    try:
        fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    if fecha_fin < fecha_inicio:
        return jsonify({'error': 'La fecha fin debe ser mayor a la fecha inicio'}), 400
    
    # Verificar que no exista una asignacion igual
    existing = Asignacion.query.filter_by(
        profesor_id=data['profesor_id'],
        materia_id=data['materia_id'],
        grupo_id=data['grupo_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Ya existe una asignación para este profesor, materia y grupo'}), 409
    
    asignacion = Asignacion(
        profesor_id=data['profesor_id'],
        materia_id=data['materia_id'],
        grupo_id=data['grupo_id'],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=data.get('activo', True)
    )
    
    db.session.add(asignacion)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating asignacion: {str(e)}')
        return jsonify({'error': f'Error al crear asignación: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Asignación creada exitosamente',
        'asignacion': asignacion.to_dict()
    }), 201


@asignaciones_bp.route('/<int:asignacion_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_asignacion(asignacion_id):
    """
    Actualiza una asignacion — scoped
    Body: { profesor_id, materia_id, grupo_id, fecha_inicio, fecha_fin, activo }
    """
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    if _asig_forbidden(asignacion):
        return jsonify({'error': 'Cross-sede forbidden', 'code': 'CROSS_SEDE'}), 403
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    if 'profesor_id' in data:
        profesor = db.session.get(Profesor, data['profesor_id'])
        if not profesor:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        asignacion.profesor_id = data['profesor_id']
    
    if 'materia_id' in data:
        materia = db.session.get(Materia, data['materia_id'])
        if not materia:
            return jsonify({'error': 'Materia no encontrada'}), 404
        asignacion.materia_id = data['materia_id']
    
    if 'grupo_id' in data:
        grupo = db.session.get(Grupo, data['grupo_id'])
        if not grupo:
            return jsonify({'error': 'Grupo no encontrado'}), 404
        asignacion.grupo_id = data['grupo_id']
    
    if 'fecha_inicio' in data:
        try:
            asignacion.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if 'fecha_fin' in data:
        try:
            asignacion.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if 'activo' in data:
        asignacion.activo = data['activo']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating asignacion: {str(e)}')
        return jsonify({'error': f'Error al actualizar asignación: {str(e)}'}), 500
    
    return jsonify({
        'message': 'Asignación actualizada exitosamente',
        'asignacion': asignacion.to_dict()
    }), 200


@asignaciones_bp.route('/<int:asignacion_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_asignacion(asignacion_id):
    """
    Elimina una asignacion — scoped
    """
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    if _asig_forbidden(asignacion):
        return jsonify({'error': 'Cross-sede forbidden', 'code': 'CROSS_SEDE'}), 403
    
    db.session.delete(asignacion)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting asignacion: {str(e)}')
        return jsonify({'error': f'Error al eliminar asignación: {str(e)}'}), 500
    
    return jsonify({'message': 'Asignación eliminada exitosamente'}), 200


# ============================================================
# VERIFICAR SI PUEDE EDITAR CALIFICACIONES
# ============================================================

@asignaciones_bp.route('/<int:asignacion_id>/puede-editar', methods=['GET'])
@jwt_required()
def puede_editar(asignacion_id):
    """
    Verifica si actualmente se puede editar calificaciones para esta asignacion
    (dentro del período fecha_inicio - fecha_fin)
    """
    asignacion = Asignacion.query.get_or_404(asignacion_id)
    
    return jsonify({
        'asignacion_id': asignacion_id,
        'puede_editar': asignacion.puede_editar_calificaciones(),
        'fecha_inicio': asignacion.fecha_inicio.isoformat() if asignacion.fecha_inicio else None,
        'fecha_fin': asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None
    }), 200


@asignaciones_bp.route('/profesor/<int:profesor_id>/actuales', methods=['GET'])
@jwt_required()
def get_asignaciones_actuales_profesor(profesor_id):
    """
    Obtiene las asignaciones actuales de un profesor
    (donde puede editar calificaciones)
    """
    from datetime import date
    
    profesor = Profesor.query.get_or_404(profesor_id)
    today = date.today()
    
    # Asignaciones donde hoy está dentro del período
    asignaciones = Asignacion.query.filter(
        Asignacion.profesor_id == profesor_id,
        Asignacion.activo == True,
        Asignacion.fecha_inicio <= today,
        Asignacion.fecha_fin >= today
    ).all()
    
    return jsonify({
        'profesor': profesor.to_dict(),
        'asignaciones': [a.to_dict() for a in asignaciones],
        'total': len(asignaciones),
        'hoy': today.isoformat()
    }), 200