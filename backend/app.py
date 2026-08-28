"""
Portal de Calificaciones - Universidad Felipe Villanueva
Backend Flask API
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from datetime import timedelta

from config import get_config
from models import db
from extensions import limiter


def create_app(config_name=None):
    """
    Factory de la aplicación Flask
    """
    # Crear carpeta instance ANTES de cargar la config
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    app = Flask(__name__)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # Cargar configuración
    if config_name:
        app.config.from_object(config_name)
    else:
        config = get_config()
        app.config.from_object(config)
    
    # Configuración adicional
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB para importación
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)
    
    # Inicializar extensiones
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3050",
        "http://127.0.0.1:3050",
        "http://89.116.51.59:3050",
        "http://89.116.51.59:5050",
        "http://localhost:5173",
        "https://alumnos.felipe-villa-nueva-teotitlan.site",
        "http://alumnos.felipe-villa-nueva-teotitlan.site",
        "https://aulas.felipe-villa-nueva-teotitlan.site",
        "http://aulas.felipe-villa-nueva-teotitlan.site",
        "https://extras.felipe-villa-nueva-teotitlan.site",
        "http://extras.felipe-villa-nueva-teotitlan.site",
    ]
    env_origins = app.config.get("CORS_ORIGINS") or []
    origins = env_origins if env_origins else default_origins
    CORS(app, 
         supports_credentials=True,
         origins=origins,
         allow_headers=["Content-Type", "Authorization", "Accept"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    JWTManager(app)
    limiter.init_app(app)
    Migrate(app, db)
    
    # Inicializar base de datos
    db.init_app(app)
    
    # Ensure wiki_attachments directory exists
    wiki_attach_path = os.path.join(os.path.dirname(__file__), 'instance', 'wiki_attachments')
    if not os.path.exists(wiki_attach_path):
        os.makedirs(wiki_attach_path, exist_ok=True)

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.alumnos import alumnos_bp
    from routes.carreras import carreras_bp
    from routes.materias import materias_bp
    from routes.calificaciones import calificaciones_bp
    from routes.pagos import pagos_bp
    from routes.export import export_bp
    from routes.admins import admins_bp
    from routes.profesores import profesores_bp
    from routes.grupos import grupos_bp
    from routes.asignaciones import asignaciones_bp
    from routes.profesor import profesor_bp
    from routes.practicas import practicas_bp
    from routes.settings import settings_bp
    from routes.imports import imports_bp
    from routes.boletas import boletas_bp
    from routes.sedes import sedes_bp
    from routes.wiki import wiki_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(alumnos_bp, url_prefix='/api/alumnos')
    app.register_blueprint(carreras_bp, url_prefix='/api/carreras')
    app.register_blueprint(materias_bp, url_prefix='/api/materias')
    app.register_blueprint(calificaciones_bp, url_prefix='/api/calificaciones')
    app.register_blueprint(pagos_bp, url_prefix='/api/pagos')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(admins_bp, url_prefix='/api/admins')
    app.register_blueprint(profesores_bp, url_prefix='/api/profesores')
    app.register_blueprint(grupos_bp, url_prefix='/api/grupos')
    app.register_blueprint(asignaciones_bp, url_prefix='/api/asignaciones')
    app.register_blueprint(profesor_bp, url_prefix='/api/profesor')
    app.register_blueprint(practicas_bp, url_prefix='/api/practicas')
    app.register_blueprint(settings_bp, url_prefix='/api/config')
    app.register_blueprint(imports_bp, url_prefix='/api/imports')
    app.register_blueprint(boletas_bp, url_prefix='/api/boletas')
    app.register_blueprint(sedes_bp, url_prefix='/api/sedes')
    app.register_blueprint(wiki_bp, url_prefix='/api/wiki')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Portal FV API',
            'version': '1.0.0'
        })
    
    # Setup endpoint (solo para crear primer admin)
    @app.route('/api/setup', methods=['GET', 'POST'])
    def setup_admin():
        """Crea el admin por defecto si no existe"""
        from models import Admin
        
        if Admin.query.first():
            return jsonify({'message': 'Ya existe un administrador'}), 200
        
        try:
            admin = Admin(
                username='admin',
                email='admin@universidadfv.edu.mx',
                nombre='Administrador Principal'
            )
            admin.set_password('admin' + '123')
            db.session.add(admin)
            db.session.commit()
            
            return jsonify({
                'message': 'Administrador creado',
                'credentials': {
                    'email': 'admin@universidadfv.edu.mx',
                    'password': 'admin' + '123'
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
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
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'error': 'El archivo excede el límite de 10MB',
            'code': 'FILE_TOO_LARGE'
        }), 413
    
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
        admin.set_password('admin' + '123')
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Default admin created - change password on first login")
    
    # Seed de configuración por defecto
    from models import Config
    defaults = {
        'smtp_host': '',
        'smtp_port': '587',
        'smtp_email': '',
        'smtp_password': '',
        'smtp_use_tls': 'true',
        'app_name': 'Portal de Calificaciones',
        'app_logo_url': '',
    }
    for key, value in defaults.items():
        if not Config.query.filter_by(key=key).first():
            db.session.add(Config(key=key, value=value))
    db.session.commit()
    print('[OK] Configuración por defecto creada')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
