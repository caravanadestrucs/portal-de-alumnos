# Portal de Calificaciones - Backend Flask

API REST para el Portal de Calificaciones de la Universidad Felipe Villanueva.

## Stack Tecnológico

- **Framework:** Flask 3.0
- **ORM:** SQLAlchemy con Flask-SQLAlchemy
- **Auth:** JWT con Flask-JWT-Extended
- **Base de datos:** SQLite (desarrollo) / MySQL (producción)
- **CORS:** Flask-CORS

## Instalación

### 1. Clonar y crear entorno virtual

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Variables de entorno (opcional)

Crear archivo `.env` en la raíz del backend:

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-secret-key-aqui
JWT_SECRET_KEY=tu-jwt-secret-aqui
PORT=5000

# Para MySQL (producción)
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=portal_user
# MYSQL_PASSWORD=tu_password
# MYSQL_DATABASE=portal_fv
```

### 4. Ejecutar la aplicación

```bash
# Modo desarrollo
python app.py

# O con Flask CLI
flask run --debug

# Especificar puerto
flask run --debug --port 3000
```

La API estará disponible en: `http://localhost:5000`

## Credenciales por Defecto

Al iniciar por primera vez, se crea un admin:

- **Email:** admin@universidadfv.edu.mx
- **Contraseña:** admin123

⚠️ **IMPORTANTE:** Cambiar la contraseña del admin inmediatamente después del primer login.

## Endpoints API

### Autenticación

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/api/auth/login` | Login admin/alumno | No |
| POST | `/api/auth/register` | Registro de alumno | No |
| POST | `/api/auth/logout` | Cerrar sesión | Sí |
| GET | `/api/auth/me` | Usuario actual | Sí |
| POST | `/api/auth/refresh` | Refrescar token | Sí |
| POST | `/api/auth/change-password` | Cambiar contraseña | Sí |

### Alumnos

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/alumnos` | Listar alumnos | Admin |
| POST | `/api/alumnos` | Crear alumno | Admin |
| GET | `/api/alumnos/<id>` | Ver alumno | Admin/Sí |
| PUT | `/api/alumnos/<id>` | Editar alumno | Admin |
| DELETE | `/api/alumnos/<id>` | Eliminar alumno | Admin |
| GET | `/api/alumnos/mis-datos` | Mis datos | Alumno |
| GET | `/api/alumnos/stats` | Estadísticas | Admin |

### Carreras

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/carreras` | Listar carreras | No |
| POST | `/api/carreras` | Crear carrera | Admin |
| GET | `/api/carreras/<id>` | Ver carrera | No |
| PUT | `/api/carreras/<id>` | Editar carrera | Admin |
| DELETE | `/api/carreras/<id>` | Eliminar carrera | Admin |
| GET | `/api/carreras/<id>/materias` | Materias de carrera | No |
| GET | `/api/carreras/<id>/alumnos` | Alumnos de carrera | No |

### Materias

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/materias` | Listar materias | No |
| POST | `/api/materias` | Crear materia | Admin |
| GET | `/api/materias/<id>` | Ver materia | No |
| PUT | `/api/materias/<id>` | Editar materia | Admin |
| DELETE | `/api/materias/<id>` | Eliminar materia | Admin |

### Calificaciones

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/calificaciones/alumno/<id>` | Calificaciones alumno | Admin/Sí |
| POST | `/api/calificaciones` | Crear/actualizar calif. | Admin |
| GET | `/api/calificaciones/alumno/<id>/historial` | Historial completo | Admin/Sí |
| GET | `/api/calificaciones/<id>` | Ver calificación | Admin/Sí |
| DELETE | `/api/calificaciones/<id>` | Eliminar calif. | Admin |
| GET | `/api/calificaciones/periodos` | Lista de periodos | No |
| POST | `/api/calificaciones/bulk` | Bulk create | Admin |

### Pagos

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/pagos/alumno/<id>` | Notas de alumno | Admin/Sí |
| POST | `/api/pagos` | Crear nota | Admin |
| GET | `/api/pagos/<id>` | Ver nota | Admin/Sí |
| PUT | `/api/pagos/<id>` | Editar nota | Admin |
| DELETE | `/api/pagos/<id>` | Eliminar nota | Admin |
| PATCH | `/api/pagos/toggle-pagado/<id>` | Toggle pagado | Admin |
| GET | `/api/pagos/resumen-general` | Resumen general | Admin |
| GET | `/api/pagos/todas` | Todas las notas | Admin |

### Exportación

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/export/sql` | Dump SQL completo | Admin |
| GET | `/api/export/excel` | Archivo Excel | Admin |
| GET | `/api/export/json` | Archivo JSON | Admin |

### Sistema

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/health` | Health check | No |

## Uso de la API

### Autenticación

Todas las rutas protegidas requieren el header:

```
Authorization: Bearer <token>
```

El token se obtiene al hacer login.

### Ejemplo con curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@universidadfv.edu.mx", "password": "admin123"}'

# Listar alumnos (con token)
curl -X GET http://localhost:5000/api/alumnos \
  -H "Authorization: Bearer <tu-token>"
```

### Ejemplo con JavaScript (fetch)

```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};

// Usar token
const response = await fetch('http://localhost:5000/api/alumnos', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

## Estructura del Proyecto

```
backend/
├── app.py              # App principal y configuración
├── config.py           # Configuraciones por entorno
├── models.py           # Modelos SQLAlchemy
├── requirements.txt    # Dependencias Python
├── instance/
│   └── portal.db       # Base de datos SQLite (generado)
├── routes/
│   ├── __init__.py
│   ├── auth.py         # Rutas de autenticación
│   ├── alumnos.py      # CRUD alumnos
│   ├── carreras.py     # CRUD carreras
│   ├── materias.py     # CRUD materias
│   ├── calificaciones.py
│   ├── pagos.py
│   └── export.py       # Exportar datos
└── utils/
    ├── __init__.py
    ├── decorators.py   # @admin_required, etc.
    └── security.py     # Hash y JWT utilities
```

## Migración a MySQL (Producción)

1. Exportar datos desde SQLite:
   ```
   GET /api/export/sql
   ```

2. Crear base de datos MySQL:
   ```sql
   CREATE DATABASE portal_fv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. Configurar variables de entorno en producción

4. Importar el dump SQL en MySQL

5. Cambiar `FLASK_ENV=production` y reiniciar

## Desarrollo

### Comandos útiles

```bash
# Reiniciar base de datos
rm instance/portal.db
python app.py

# Ver rutas disponibles
flask routes

# Shell interactivo con contexto
flask shell
>>> from app import app
>>> from models import db, Admin, Alumno
>>> db.create_all()
```

### Tests

```bash
pip install pytest pytest-flask
pytest
```

## Seguridad

- Contraseñas hasheadas con bcrypt (12 rounds)
- Tokens JWT con expiración de 24 horas
- CORS configurado
- Validación de inputs en backend
- SQLAlchemy ORM (previene SQL injection)

## Licencia

Proprietario - Universidad Felipe Villanueva
