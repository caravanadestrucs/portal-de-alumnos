"""
Rutas para generación y descarga de boletas de calificaciones
"""
import io
import os
import logging
from datetime import datetime
from zipfile import ZipFile
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Alumno, Calificacion, Materia, Carrera
from utils.decorators import admin_required

boletas_bp = Blueprint('boletas', __name__)

# ============================================================
# GET /api/boletas/alumnos
# Lista alumnos con sus calificaciones para generar boletas
# Query params: carrera_id, cuatrimestre, periodo
# ============================================================
@boletas_bp.route('/alumnos', methods=['GET'])
@jwt_required()
@admin_required
def listar_alumnos_boletas():
    carrera_id = request.args.get('carrera_id', type=int)
    grupo_id = request.args.get('grupo_id', type=int)
    search = request.args.get('search', '').strip()
    
    query = Alumno.query.filter_by(activo=True)
    
    if carrera_id:
        query = query.filter_by(carrera_id=carrera_id)
    
    if grupo_id:
        from models import GrupoIntegrante
        alumno_ids = db.session.query(GrupoIntegrante.alumno_id).filter_by(grupo_id=grupo_id)
        query = query.filter(Alumno.id.in_(alumno_ids))
    
    if search:
        query = query.filter(
            db.or_(
                Alumno.nombre.ilike(f'%{search}%'),
                Alumno.apellido_paterno.ilike(f'%{search}%'),
                Alumno.apellido_materno.ilike(f'%{search}%'),
                Alumno.numero_control.ilike(f'%{search}%')
            )
        )
    
    alumnos = query.order_by(Alumno.apellido_paterno, Alumno.nombre).all()
    
    result = []
    for a in alumnos:
        # Contar calificaciones con nota
        calif_count = Calificacion.query.filter(
            Calificacion.alumno_id == a.id,
            Calificacion.calificacion_final > 0
        ).count()
        
        result.append({
            'id': a.id,
            'numero_control': a.numero_control,
            'nombre_completo': a.nombre_completo,
            'carrera_id': a.carrera_id,
            'carrera_nombre': a.carrera.nombre if a.carrera else '',
            'calificaciones_count': calif_count,
        })
    
    return jsonify({'alumnos': result})


# ============================================================
# GET /api/boletas/download/<alumno_id>
# Descarga una boleta individual en .docx
# ============================================================
@boletas_bp.route('/download/<int:alumno_id>', methods=['GET'])
@jwt_required()
@admin_required
def descargar_boleta(alumno_id):
    alumno = db.session.get(Alumno, alumno_id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    carrera = db.session.get(Carrera, alumno.carrera_id)
    
    # Obtener calificaciones del alumno con materia cargada
    calificaciones = Calificacion.query.options(
        db.joinedload(Calificacion.materia)
    ).filter(
        Calificacion.alumno_id == alumno_id,
        Calificacion.calificacion_final > 0
    ).order_by(
        Calificacion.materia_id
    ).all()
    
    if not calificaciones:
        return jsonify({'error': 'El alumno no tiene calificaciones registradas'}), 400
    
    # Obtener configuración
    from models import Config
    config_db = {c.key: c.value for c in Config.query.all()}
    
    # Generar boleta
    from utils.boleta_generator import generar_boleta
    doc = generar_boleta(alumno, calificaciones, carrera, config_db)
    
    # Guardar en buffer
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    
    # Nombre del archivo
    nombre_archivo = f"BOLETA_{alumno.numero_control or alumno_id}_{alumno.apellido_paterno}_{alumno.nombre}.docx"
    nombre_archivo = nombre_archivo.replace(' ', '_').upper()
    
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=nombre_archivo
    )


# ============================================================
# GET /api/boletas/download-multiple
# Descarga múltiples boletas en un ZIP
# Query params: alumno_ids (comma-separated)
# ============================================================
@boletas_bp.route('/download-multiple', methods=['GET'])
@jwt_required()
@admin_required
def descargar_boletas_multiples():
    alumno_ids_str = request.args.get('alumno_ids', '')
    if not alumno_ids_str:
        return jsonify({'error': 'Debes proporcionar al menos un alumno'}), 400
    
    try:
        alumno_ids = [int(x.strip()) for x in alumno_ids_str.split(',') if x.strip()]
    except ValueError:
        return jsonify({'error': 'IDs de alumno inválidos'}), 400
    
    from models import Config
    config_db = {c.key: c.value for c in Config.query.all()}
    from utils.boleta_generator import generar_boleta
    
    zip_buf = io.BytesIO()
    
    with ZipFile(zip_buf, 'w') as zf:
        for aid in alumno_ids:
            alumno = db.session.get(Alumno, aid)
            if not alumno:
                continue
            
            carrera = db.session.get(Carrera, alumno.carrera_id)
            
            calificaciones = Calificacion.query.options(
                db.joinedload(Calificacion.materia)
            ).filter(
                Calificacion.alumno_id == aid,
                Calificacion.calificacion_final > 0
            ).order_by(Calificacion.materia_id).all()
            
            if not calificaciones:
                continue
            
            doc = generar_boleta(alumno, calificaciones, carrera, config_db)
            
            doc_buf = io.BytesIO()
            doc.save(doc_buf)
            doc_buf.seek(0)
            
            nombre_archivo = f"BOLETA_{alumno.numero_control or aid}_{alumno.apellido_paterno}_{alumno.nombre}.docx"
            nombre_archivo = nombre_archivo.replace(' ', '_').upper()
            
            zf.writestr(nombre_archivo, doc_buf.getvalue())
    
    zip_buf.seek(0)
    
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'BOLETAS_{datetime.now().strftime("%Y%m%d")}.zip'
    )


# ============================================================
# GET /api/boletas/preview/<alumno_id>
# Vista previa de datos de la boleta (para mostrar en pantalla)
# ============================================================
@boletas_bp.route('/preview/<int:alumno_id>', methods=['GET'])
@jwt_required()
@admin_required
def vista_previa_boleta(alumno_id):
    alumno = db.session.get(Alumno, alumno_id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    carrera = db.session.get(Carrera, alumno.carrera_id)
    
    calificaciones = Calificacion.query.options(
        db.joinedload(Calificacion.materia)
    ).filter(
        Calificacion.alumno_id == alumno_id,
        Calificacion.calificacion_final > 0
    ).order_by(Calificacion.materia_id).all()
    
    calif_list = []
    for c in calificaciones:
        calif_list.append({
            'materia': c.materia.nombre if c.materia else 'N/A',
            'calificacion': c.calificacion_final,
            'periodo': c.periodo,
            'anio': c.anio,
        })
    
    calif_validas = [c.calificacion_final for c in calificaciones if c.calificacion_final > 0]
    promedio = round(sum(calif_validas) / len(calif_validas), 1) if calif_validas else 0
    aprobadas = sum(1 for c in calif_validas if c >= 8)
    
    return jsonify({
        'alumno': {
            'id': alumno.id,
            'nombre_completo': alumno.nombre_completo,
            'numero_control': alumno.numero_control,
            'carrera': carrera.nombre if carrera else '',
        },
        'calificaciones': calif_list,
        'promedio': promedio,
        'materias_aprobadas': aprobadas,
        'total_materias': len(calif_validas),
    })
