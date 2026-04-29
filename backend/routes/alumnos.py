"""
Rutas para gestión de Alumnos
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models import db, Alumno, Carrera, Calificacion
from utils.decorators import admin_required, get_admin_or_403

alumnos_bp = Blueprint('alumnos', __name__)


@alumnos_bp.route('', methods=['GET'])
@admin_required
def list_alumnos():
    """
    Lista todos los alumnos (admin)
    Query params: 
        - search: búsqueda por nombre/numero_control/email
        - carrera_id: filtrar por carrera
        - activo: true/false
        - page: número de página
        - per_page: items por página
    """
    # Obtener parámetros de query
    search = request.args.get('search', '').strip()
    carrera_id = request.args.get('carrera_id', type=int)
    activo = request.args.get('activo')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Query base
    query = Alumno.query
    
    # Aplicar filtros
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Alumno.nombre.ilike(search_term),
                Alumno.apellido_paterno.ilike(search_term),
                Alumno.apellido_materno.ilike(search_term),
                Alumno.numero_control.ilike(search_term),
                Alumno.email.ilike(search_term)
            )
        )
    
    if carrera_id:
        query = query.filter(Alumno.carrera_id == carrera_id)
    
    if activo is not None:
        query = query.filter(Alumno.activo == (activo.lower() == 'true'))
    
    # Ordenar por nombre
    query = query.order_by(Alumno.apellido_paterno, Alumno.nombre)
    
    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'alumnos': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@alumnos_bp.route('', methods=['POST'])
@admin_required
def create_alumno():
    """
    Crea un nuevo alumno (admin)
    Body: {
        numero_control, nombre, apellido_paterno, apellido_materno,
        email, password, carrera_id, activo
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    # Validaciones
    required_fields = ['numero_control', 'nombre', 'apellido_paterno', 'email', 'password', 'carrera_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar número de control único
    if Alumno.query.filter_by(numero_control=data['numero_control']).first():
        return jsonify({'error': 'El número de control ya existe'}), 409
    
    # Verificar email único
    if Alumno.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'El email ya existe'}), 409
    
    # Verificar que la carrera exista
    carrera = Carrera.query.get(data['carrera_id'])
    if not carrera:
        return jsonify({'error': 'La carrera especificada no existe'}), 404
    
    try:
        alumno = Alumno(
            numero_control=data['numero_control'],
            nombre=data['nombre'].strip(),
            apellido_paterno=data['apellido_paterno'].strip(),
            apellido_materno=data.get('apellido_materno', '').strip() or None,
            email=data['email'].lower().strip(),
            carrera_id=data['carrera_id'],
            activo=data.get('activo', True),
            fecha_registro=datetime.utcnow().date()
        )
        alumno.set_password(data['password'])
        
        db.session.add(alumno)
        db.session.commit()
        
        return jsonify({
            'message': 'Alumno creado exitosamente',
            'alumno': alumno.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear alumno: {str(e)}'}), 500


@alumnos_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_alumno(id):
    """
    Obtiene un alumno por ID (admin o el propio alumno)
    """
    identity = get_jwt_identity()
    alumno = Alumno.query.get_or_404(id)
    
    # Verificar permisos: solo el admin o el propio alumno pueden ver
    if identity.get('type') == 'alumno' and identity['id'] != id:
        return jsonify({'error': 'No tienes permiso para ver este alumno'}), 403
    
    return jsonify({'alumno': alumno.to_dict()}), 200


@alumnos_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_alumno(id):
    """
    Actualiza un alumno (admin)
    Si se cambia la carrera, se eliminan las calificaciones anteriores
    (porque pertenecían a la carrera anterior).
    """
    alumno = Alumno.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos requeridos'}), 400
    
    try:
        carrera_cambiada = False
        antigua_carrera_id = alumno.carrera_id
        
        # Actualizar campos
        if 'nombre' in data:
            alumno.nombre = data['nombre'].strip()
        if 'apellido_paterno' in data:
            alumno.apellido_paterno = data['apellido_paterno'].strip()
        if 'apellido_materno' in data:
            alumno.apellido_materno = data['apellido_materno'].strip() or None
        if 'email' in data:
            new_email = data['email'].lower().strip()
            if new_email != alumno.email:
                if Alumno.query.filter_by(email=new_email).first():
                    return jsonify({'error': 'El email ya está en uso'}), 409
                alumno.email = new_email
        if 'carrera_id' in data:
            nueva_carrera_id = int(data['carrera_id'])
            if nueva_carrera_id != alumno.carrera_id:
                carrera = Carrera.query.get(nueva_carrera_id)
                if not carrera:
                    return jsonify({'error': 'La carrera especificada no existe'}), 404
                alumno.carrera_id = nueva_carrera_id
                carrera_cambiada = True
        if 'activo' in data:
            alumno.activo = bool(data['activo'])
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
            alumno.set_password(data['password'])
        
        # Requisitos de titulación
        if 'servicio_social' in data:
            alumno.servicio_social = bool(data['servicio_social'])
        if 'examen_idiomas' in data:
            alumno.examen_idiomas = bool(data['examen_idiomas'])
        if 'credenciales_completas' in data:
            alumno.credenciales_completas = bool(data['credenciales_completas'])
        if 'documentacion_completa' in data:
            alumno.documentacion_completa = bool(data['documentacion_completa'])
        
        # Si cambió de carrera, eliminar calificaciones anteriores
        calificaciones_eliminadas = 0
        if carrera_cambiada:
            calificaciones_eliminadas = Calificacion.query.filter_by(alumno_id=id).delete()
        
        db.session.commit()
        
        response_data = {
            'message': 'Alumno actualizado exitosamente',
            'alumno': alumno.to_dict()
        }
        if carrera_cambiada:
            response_data['calificaciones_eliminadas'] = calificaciones_eliminadas
            response_data['warning'] = 'Se eliminaron las calificaciones anteriores al cambiar de carrera'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar alumno: {str(e)}'}), 500


@alumnos_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_alumno(id):
    """
    Elimina un alumno (admin)
    """
    alumno = Alumno.query.get_or_404(id)
    
    try:
        # Eliminar registros relacionados (redundante con cascade, pero seguro)
        from models import Calificacion, GrupoIntegrante, PracticaProfesional, NotaRemision
        
        Calificacion.query.filter_by(alumno_id=id).delete()
        GrupoIntegrante.query.filter_by(alumno_id=id).delete()
        PracticaProfesional.query.filter_by(alumno_id=id).delete()
        NotaRemision.query.filter_by(alumno_id=id).delete()
        
        db.session.delete(alumno)
        db.session.commit()
        
        return jsonify({'message': 'Alumno eliminado exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar alumno: {str(e)}'}), 500


@alumnos_bp.route('/mis-datos', methods=['GET'])
@jwt_required()
def mis_datos():
    """
    Obtiene los datos del alumno logueado (alumno only)
    """
    identity = get_jwt_identity()
    
    if identity.get('type') != 'alumno':
        return jsonify({'error': 'Solo alumnos pueden acceder a esta ruta'}), 403
    
    alumno = Alumno.query.get_or_404(identity['id'])
    
    # Incluir estadísticas
    num_calificaciones = alumno.calificaciones.count()
    num_practicas = alumno.practicas.count()
    practicas_completadas = alumno.practicas.filter_by(validada=True).count()
    
    return jsonify({
        'alumno': alumno.to_dict(),
        'estadisticas': {
            'calificaciones_registradas': num_calificaciones,
            'practicas_totales': num_practicas,
            'practicas_completadas': practicas_completadas
        }
    }), 200


@alumnos_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    Estadísticas generales de alumnos (admin)
    """
    total = Alumno.query.count()
    activos = Alumno.query.filter_by(activo=True).count()
    inactivos = Alumno.query.filter_by(activo=False).count()
    
    # Alumnos por carrera
    from sqlalchemy import func
    por_carrera = db.session.query(
        Carrera.nombre,
        func.count(Alumno.id).label('total')
    ).join(Alumno).group_by(Carrera.id).all()
    
    return jsonify({
        'total': total,
        'activos': activos,
        'inactivos': inactivos,
        'por_carrera': [{'carrera': c, 'total': t} for c, t in por_carrera]
    }), 200
