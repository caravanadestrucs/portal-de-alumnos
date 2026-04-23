"""
Portal de Calificaciones - Universidad Felipe Villanueva
Backend Flask API
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from datetime import timedelta

from config import get_config
from models import db, init_db


def create_app(config_name=None):
    """
    Factory de la aplicación Flask
    """
    # Crear carpeta instance ANTES de cargar la config
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    app = Flask(__name__)
    
    # Cargar configuración
    if config_name:
        app.config.from_object(config_name)
    else:
        config = get_config()
        app.config.from_object(config)
    
    # Configuración adicional
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Inicializar extensiones
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)
    Migrate(app, db)
    
    # Inicializar base de datos
    db.init_app(app)
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.alumnos import alumnos_bp
    from routes.carreras import carreras_bp
    from routes.materias import materias_bp
    from routes.calificaciones import calificaciones_bp
    from routes.pagos import pagos_bp
    from routes.export import export_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(alumnos_bp, url_prefix='/api/alumnos')
    app.register_blueprint(carreras_bp, url_prefix='/api/carreras')
    app.register_blueprint(materias_bp, url_prefix='/api/materias')
    app.register_blueprint(calificaciones_bp, url_prefix='/api/calificaciones')
    app.register_blueprint(pagos_bp, url_prefix='/api/pagos')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Portal FV API',
            'version': '1.0.0'
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Portal de Calificaciones - Universidad Felipe Villanueva',
            'version': '1.0.0',
            'docs': '/api/docs'
        })
    
    # Manejo de errores
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Solicitud incorrecta',
            'message': str(error.description) if hasattr(error, 'description') else 'Bad request',
            'code': 'BAD_REQUEST'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'No autorizado',
            'message': 'Token inválido o expirado',
            'code': 'UNAUTHORIZED'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Prohibido',
            'message': 'No tienes permisos para acceder a este recurso',
            'code': 'FORBIDDEN'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'No encontrado',
            'message': 'El recurso solicitado no existe',
            'code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'error': 'Conflicto',
            'message': str(error.description) if hasattr(error, 'description') else 'Recurso duplicado',
            'code': 'CONFLICT'
        }), 409
    
    @app.errorhandler(422)
    def validation_error(error):
        return jsonify({
            'error': 'Error de validación',
            'message': str(error.description) if hasattr(error, 'description') else 'Datos inválidos',
            'code': 'VALIDATION_ERROR'
        }), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Error interno del servidor',
            'message': 'Algo salió mal. Intenta de nuevo más tarde.',
            'code': 'INTERNAL_ERROR'
        }), 500
    
    return app


# Crear aplicación
app = create_app()

# Inicializar base de datos (crea tablas y admin por defecto)
with app.app_context():
    db.create_all()
    
    # Crear admin por defecto si no existe
    from models import Admin
    if not Admin.query.first():
        admin = Admin(
            username='admin',
            email='admin@universidadfv.edu.mx',
            nombre='Administrador Principal'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('[OK] Admin por defecto creado')
        print('   Email: admin@universidadfv.edu.mx')
        print('   Contrasena: admin123')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
