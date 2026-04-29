"""
Rutas para gestión de Pagos (Notas de Remisión)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models import db, NotaRemision, Alumno, Admin
from utils.decorators import admin_required

pagos_bp = Blueprint('pagos', __name__)


@pagos_bp.route('/alumnos/<int:alumno_id>', methods=['GET'])
# @jwt_required()
def get_alumno_pagos(alumno_id):
    """
    Obtiene todas las notas de remisión de un alumno
    """
    # Verificar permisos (si hay JWT)
    try:
        identity = get_jwt_identity()
        if identity and identity.get('type') == 'alumno' and identity['id'] != alumno_id:
            return jsonify({'error': 'No tienes permiso para ver estos pagos'}), 403
    except:
        pass
    
    alumno = Alumno.query.get_or_404(alumno_id)
    
    # Filtros
    pagada = request.args.get('pagada')
    
    query = NotaRemision.query.filter_by(alumno_id=alumno_id)
    
    if pagada is not None:
        query = query.filter(NotaRemision.pagada == (pagada.lower() == 'true'))
    
    notas = query.order_by(NotaRemision.fecha_emision.desc()).all()
    
    # Calcular totales
    total_adeudo = sum(n.monto for n in notas if not n.pagada)
    total_pagado = sum(n.monto for n in notas if n.pagada)
    
    return jsonify({
        'alumno': alumno.to_dict_public(),
        'notas': [n.to_dict() for n in notas],
        'resumen': {
            'total_notas': len(notas),
            'pendientes': sum(1 for n in notas if not n.pagada),
            'pagadas': sum(1 for n in notas if n.pagada),
            'total_adeudo': round(total_adeudo, 2),
            'total_pagado': round(total_pagado, 2)
        }
    }), 200


@pagos_bp.route('', methods=['POST'])
# @admin_required
def create_nota():
    """
    Crea una nueva nota de remisión (admin)
    Body: { alumno_id, concepto, monto, fecha_emision, fecha_corte }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    if not data.get('alumno_id'):
        return jsonify({'error': 'El alumno es requerido'}), 400
    if not data.get('concepto'):
        return jsonify({'error': 'El concepto es requerido'}), 400
    if not data.get('monto'):
        return jsonify({'error': 'El monto es requerido'}), 400
    
    # Verificar que el alumno exista
    alumno = Alumno.query.get(data['alumno_id'])
    if not alumno:
        return jsonify({'error': 'El alumno no existe'}), 404
    
    # Intentar obtener el admin (si no hay JWT, usar admin con id=1)
    try:
        identity = get_jwt_identity()
        created_by_id = identity.get('id', 1) if identity else 1
    except:
        created_by_id = 1
    
    try:
        fecha_emision = datetime.utcnow().date()
        if data.get('fecha_emision'):
            fecha_emision = datetime.fromisoformat(data['fecha_emision']).date()
        
        fecha_corte = None
        if data.get('fecha_corte'):
            fecha_corte = datetime.fromisoformat(data['fecha_corte']).date()
        
        nota = NotaRemision(
            alumno_id=data['alumno_id'],
            concepto=data['concepto'].strip(),
            monto=float(data['monto']),
            fecha_emision=fecha_emision,
            fecha_corte=fecha_corte,
            pagada=False,
            created_by_id=created_by_id
        )
        
        db.session.add(nota)
        db.session.commit()
        
        return jsonify({
            'message': 'Nota de remisión creada exitosamente',
            'nota': nota.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear nota: {str(e)}'}), 500


@pagos_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_nota(id):
    """
    Actualiza una nota de remisión (admin)
    """
    nota = NotaRemision.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    try:
        if 'concepto' in data:
            nota.concepto = data['concepto'].strip()
        if 'monto' in data:
            nota.monto = float(data['monto'])
        if 'pagada' in data:
            nota.pagada = bool(data['pagada'])
            if nota.pagada and not nota.fecha_pago:
                nota.fecha_pago = datetime.utcnow().date()
            elif not nota.pagada:
                nota.fecha_pago = None
        if 'fecha_emision' in data:
            nota.fecha_emision = datetime.fromisoformat(data['fecha_emision']).date()
        if 'fecha_corte' in data:
            nota.fecha_corte = datetime.fromisoformat(data['fecha_corte']).date() if data['fecha_corte'] else None
        if 'fecha_pago' in data:
            nota.fecha_pago = datetime.fromisoformat(data['fecha_pago']).date() if data['fecha_pago'] else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Nota de remisión actualizada exitosamente',
            'nota': nota.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar nota: {str(e)}'}), 500


@pagos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_nota(id):
    """
    Obtiene una nota por ID
    """
    nota = NotaRemision.query.get_or_404(id)
    
    identity = get_jwt_identity()
    if identity.get('type') == 'alumno' and identity['id'] != nota.alumno_id:
        return jsonify({'error': 'No tienes permiso para ver esta nota'}), 403
    
    return jsonify({'nota': nota.to_dict()}), 200


@pagos_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_nota(id):
    """
    Elimina una nota de remisión (admin)
    """
    nota = NotaRemision.query.get_or_404(id)
    
    try:
        db.session.delete(nota)
        db.session.commit()
        
        return jsonify({'message': 'Nota de remisión eliminada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar nota: {str(e)}'}), 500


@pagos_bp.route('/toggle-pagado/<int:id>', methods=['PATCH'])
# @admin_required
def toggle_pagado(id):
    """
    Cambia el estado de pagado/no pagado de una nota (admin)
    """
    nota = NotaRemision.query.get_or_404(id)
    data = request.get_json() or {}
    
    try:
        nota.pagada = not nota.pagada
        if nota.pagada:
            if data.get('fecha_pago'):
                nota.fecha_pago = datetime.fromisoformat(data['fecha_pago']).date()
            else:
                nota.fecha_pago = datetime.utcnow().date()
        else:
            nota.fecha_pago = None
        
        db.session.commit()
        
        return jsonify({
            'message': f'Nota marcada como {"pagada" if nota.pagada else "pendiente"}',
            'nota': nota.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar: {str(e)}'}), 500


@pagos_bp.route('/marcar-pagado/<int:id>', methods=['PATCH'])
@admin_required
def marcar_pagado(id):
    """
    Marca una nota como pagada con fecha específica (admin)
    Body: { "fecha_pago": "2026-04-23" }
    """
    nota = NotaRemision.query.get_or_404(id)
    data = request.get_json()
    
    if not data or not data.get('fecha_pago'):
        return jsonify({'error': 'La fecha de pago es requerida'}), 400
    
    try:
        nota.pagada = True
        nota.fecha_pago = datetime.fromisoformat(data['fecha_pago']).date()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Nota marcada como pagada',
            'nota': nota.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar: {str(e)}'}), 500


@pagos_bp.route('/resumen-general', methods=['GET'])
@admin_required
def get_resumen_general():
    """
    Resumen general de todas las notas (admin)
    """
    total_notas = NotaRemision.query.count()
    notas_pendientes = NotaRemision.query.filter_by(pagada=False).count()
    notas_pagadas = NotaRemision.query.filter_by(pagada=True).count()
    
    # Calcular totales
    from sqlalchemy import func
    
    resultado = db.session.query(
        func.sum(NotaRemision.monto).label('total')
    ).filter_by(pagada=False).first()
    
    total_adeudo = float(resultado.total) if resultado.total else 0
    
    resultado_pagado = db.session.query(
        func.sum(NotaRemision.monto).label('total')
    ).filter_by(pagada=True).first()
    
    total_pagado = float(resultado_pagado.total) if resultado_pagado.total else 0
    
    return jsonify({
        'total_notas': total_notas,
        'notas_pendientes': notas_pendientes,
        'notas_pagadas': notas_pagadas,
        'total_adeudo': round(total_adeudo, 2),
        'total_pagado': round(total_pagado, 2)
    }), 200


@pagos_bp.route('/todas', methods=['GET'])
@admin_required
def get_all_notas():
    """
    Lista todas las notas con filtros (admin)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagada = request.args.get('pagada')
    search = request.args.get('search', '')
    
    query = NotaRemision.query
    
    if pagada is not None:
        query = query.filter(NotaRemision.pagada == (pagada.lower() == 'true'))
    
    if search:
        search_term = f'%{search}%'
        from models import Alumno
        query = query.join(Alumno).filter(
            db.or_(
                Alumno.nombre.ilike(search_term),
                Alumno.apellido_paterno.ilike(search_term),
                Alumno.numero_control.ilike(search_term),
                NotaRemision.concepto.ilike(search_term)
            )
        )
    
    pagination = query.order_by(NotaRemision.fecha_emision.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'notas': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@pagos_bp.route('/alumnos-pendientes', methods=['GET'])
# @admin_required
def get_alumnos_pendientes():
    """
    Lista alumnos con pagos pendientes y su total
    """
    # Buscar alumnos que tengan al menos una nota pendiente
    subquery = db.session.query(NotaRemision.alumno_id).filter(
        NotaRemision.pagada == False
    ).distinct()
    
    alumnos_pendientes = Alumno.query.filter(
        Alumno.id.in_(subquery)
    ).all()
    
    result = []
    for alumno in alumnos_pendientes:
        notas = NotaRemision.query.filter_by(
            alumno_id=alumno.id,
            pagada=False
        ).all()
        
        total_pendiente = sum(n.monto for n in notas)
        num_notas = len(notas)
        tiene_mora = any(
            n.fecha_corte and n.fecha_corte < datetime.utcnow().date() and not n.pagada
            for n in notas
        )
        
        # Calcular mora total
        mora_total = 0
        for n in notas:
            if n.fecha_corte and not n.pagada:
                hoy = datetime.utcnow().date()
                if n.fecha_corte < hoy:
                    dias = (hoy - n.fecha_corte).days
                    mora_total += dias * 5
        
        result.append({
            'id': alumno.id,
            'numero_control': alumno.numero_control,
            'nombre': alumno.nombre_completo,
            'carrera': alumno.carrera.nombre if alumno.carrera else None,
            'total_pendiente': round(total_pendiente + mora_total, 2),
            'total_sin_mora': round(total_pendiente, 2),
            'mora_total': round(mora_total, 2),
            'num_notas': num_notas,
            'tiene_mora': tiene_mora
        })
    
    # Ordenar por total pendiente descendente
    result.sort(key=lambda x: x['total_pendiente'], reverse=True)
    
    return jsonify({
        'alumnos': result,
        'total_alumnos': len(result),
        'total_adeudo': round(sum(a['total_pendiente'] for a in result), 2)
    }), 200
