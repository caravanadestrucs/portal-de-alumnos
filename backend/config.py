"""
Configuración de la aplicación Portal FV
Desarrollo: SQLite | Producción: MySQL
"""
import os
from datetime import timedelta


class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class DevelopmentConfig(Config):
    """Configuración de desarrollo - SQLite"""
    DEBUG = True
    ENV = 'development'
    
    # Usar DATABASE_URL si está definida (Docker), sino usar path local
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Windows local path
        _db_path = r'C:\Users\Dario\Desktop\portal de alumnos\backend\instance\portal.db'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path}'
    
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Configuración de producción - MySQL"""
    DEBUG = False
    ENV = 'production'
    
    # MySQL connection string
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'portal_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'portal_fv')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )


class TestingConfig(Config):
    """Configuración de tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Mapeo de configuraciones por entorno
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Obtiene la configuración según el entorno"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
