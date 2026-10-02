"""
Resolución de la URL pública del frontend para links en emails.

Orden de precedencia:
1. Variable de entorno FRONTEND_URL (definida en docker-compose / .env)
2. Clave `frontend_url` en la tabla Config (configurable desde el panel sin redeploy)
3. Fallback localhost:5173 (solo desarrollo)

Sin esta resolución centralizada, un despliegue sin FRONTEND_URL genera
silenciosamente links a http://localhost:5173 en los emails de producción.
"""
import os


def get_frontend_url() -> str:
    """Retorna la URL base del frontend (sin slash final). Nunca lanza."""
    env_url = os.environ.get('FRONTEND_URL', '').strip().rstrip('/')
    if env_url:
        return env_url

    try:
        from models import Config
        cfg = Config.query.filter_by(key='frontend_url').first()
        if cfg and cfg.value and cfg.value.strip():
            return cfg.value.strip().rstrip('/')
    except Exception:
        # Sin app context o tabla ausente: caer al default de desarrollo
        pass

    return 'http://localhost:5173'