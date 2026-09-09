"""
Rutas para el catálogo de Períodos
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db, Periodo
from utils.decorators import admin_required

periodos_bp = Blueprint('periodos', __name__)


def _parse_fecha_opt(value, campo):
    if value in (None, ''):
        return None, None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date(), None
    except ValueError:
        return None, (jsonify({'error': f'Formato inválido en {campo}. Use YYYY-MM-DD'}), 400)


def _parse_activa(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ('true', '1'):
            return True
        if v in ('false', '0'):
            return False
        return bool(v)
    return bool(value)


@periodos_bp.route('', methods=['GET'])
@jwt_required()
def listar_periodos():
    periodos = Periodo.query.order_by(Periodo.nombre.asc()).all()
    return jsonify({'periodos': [p.to_dict() for p in periodos]}), 200


@periodos_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def crear_periodo():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Datos requeridos'}), 400
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'El campo nombre es requerido'}), 422
    if Periodo.query.filter_by(nombre=nombre).first():
        return jsonify({'error': 'Periodo ya existe'}), 409
    fecha_inicio, err = _parse_fecha_opt(data.get('fecha_inicio'), 'fecha_inicio')
    if err:
        return err
    fecha_fin, err = _parse_fecha_opt(data.get('fecha_fin'), 'fecha_fin')
    if err:
        return err
    periodo = Periodo(nombre=nombre, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                      activa=_parse_activa(data.get('activa', True)))
    db.session.add(periodo)
    db.session.commit()
    return jsonify({'message': 'Período creado exitosamente', 'periodo': periodo.to_dict()}), 201


@periodos_bp.route('/<int:periodo_id>', methods=['PUT'])
@jwt_required()
@admin_required
def actualizar_periodo(periodo_id):
    periodo = Periodo.query.get_or_404(periodo_id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Datos requeridos'}), 400
    if 'nombre' in data:
        nombre = (data.get('nombre') or '').strip()
        if not nombre:
            return jsonify({'error': 'El campo nombre es requerido'}), 422
        otro = Periodo.query.filter_by(nombre=nombre).first()
        if otro and otro.id != periodo.id:
            return jsonify({'error': 'Periodo ya existe'}), 409
        periodo.nombre = nombre
    if 'fecha_inicio' in data:
        fecha_inicio, err = _parse_fecha_opt(data.get('fecha_inicio'), 'fecha_inicio')
        if err:
            return err
        periodo.fecha_inicio = fecha_inicio
    if 'fecha_fin' in data:
        fecha_fin, err = _parse_fecha_opt(data.get('fecha_fin'), 'fecha_fin')
        if err:
            return err
        periodo.fecha_fin = fecha_fin
    if 'activa' in data:
        periodo.activa = _parse_activa(data['activa'])
    db.session.commit()
    return jsonify({'message': 'Período actualizado exitosamente', 'periodo': periodo.to_dict()}), 200


@periodos_bp.route('/<int:periodo_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def eliminar_periodo(periodo_id):
    periodo = Periodo.query.get_or_404(periodo_id)
    periodo.activa = False
    db.session.commit()
    return jsonify({'message': 'Período desactivado', 'periodo': periodo.to_dict()}), 200
