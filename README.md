# Portal de Calificaciones - Universidad Felipe Villanueva

Sistema integral de gestión académica y administrativa para la Universidad Felipe Villanueva.

## 🎯 Objetivo

Plataforma web que permite a:
- **Alumnos**: Consultar calificaciones, pagos y requisitos de titulación
- **Profesores**: Gestionar calificaciones de sus grupos asignados
- **Administradores**: CRUD completo de alumnos, profesores, materias, grupos y pagos

## 🏗️ Arquitectura

```
portal de alumnos/
├── backend/          # API REST con Flask
│   ├── app.py
│   ├── models.py      # Modelos: Alumno, Profesor, Calificacion, Pagos, etc.
│   ├── routes/         # Endpoints organizados por entidad
│   └── requirements.txt
├── frontend/         # SPA con React + Vite
│   ├── src/
│   │   ├── components/  # UI reutilizable (Card, Button, Modal, etc.)
│   │   ├── pages/       # Vistas organizadas por rol
│   │   └── context/    # AuthContext (JWT)
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🚀 Tecnologías

### Backend
- **Python 3.10** + **Flask**
- **SQLAlchemy** (ORM) + **SQLite** (desarrollo)
- **Flask-JWT-Extended** para autenticación
- **bcrypt** para hash de contraseñas

### Frontend
- **React 18** + **Vite** (build rápido)
- **React Router DOM v6** (ruteo)
- **Axios** para API calls
- **lucide-react** (iconos)
- **Tailwind CSS** (estilos utilitarios)

### DevOps
- **Docker** + **Docker Compose**
- **Nginx** (para producción, opcional)

## 📦 Instalación

### Opción 1: Docker (Recomendado)
```bash
# Clonar el proyecto
cd "C:\Users\Dario\Desktop\portal de alumnos"

# Iniciar todos los servicios
docker-compose up --build

# Acceder:
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

### Opción 2: Desarrollo Local

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

## 🔐 Credenciales por Defecto

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Admin | admin@universidadfv.edu.mx | admin123 |
| Alumno | juan.perez.test99@test.com | juanperez |

## 📋 Modelo de Datos

### Entidades Principales
- **Alumno**: numero_control, nombre, email, carrera, requisitos de titulación
- **Profesor**: numero_empleado, nombre, titulo
- **Carrera**: 6 carreras (Sistemas, Contaduría, Derecho, Pedagogía, Psicología, Ciencias del Deporte)
- **Materia**: 270 materias (45 por carrera, 9 cuatrimestres)
- **Grupo**: Relación carrera + generación
- **Asignacion**: Profesor + Materia + Grupo + fechas (limita edición)
- **Calificacion**: Asistencia (5), Prácticas (2), Extra (2), Final (escala 0-10)
- **NotaRemision**: Pagos (monto, fechas, estado)
- **PracticaProfesional**: Empresa, horas, fechas, estado

### Relaciones
```
Alumno → Carrera (N:1)
Alumno → GrupoIntegrante → Grupo (N:M)
Alumno → Calificacion ← Materia (N:M)
Alumno → PracticaProfesional (1:N)
Alumno → NotaRemision (1:N)
Profesor → Asignacion → Materia + Grupo (1:N)
```

## 🎨 Funcionalidades por Rol

### Admin
- ✅ Dashboard con estadísticas
- ✅ CRUD Alumnos (con reset de contraseña)
- ✅ CRUD Profesores
- ✅ CRUD Carreras (6 carreras precargadas)
- ✅ CRUD Materias (270 materias precargadas)
- ✅ CRUD Grupos (asignar alumnos por carrera)
- ✅ CRUD Asignaciones (profesor + materia + grupo con fechas)
- ✅ Gestión de Calificaciones (edicion masiva)
- ✅ Gestión de Pagos (notas de remisión)
- ✅ Requisitos de Titulación (servicio social, idiomas, prácticas)
- ✅ Exportar datos

### Profesor
- ✅ Dashboard con sus asignaciones
- ✅ Ver alumnos por grupo asignado
- ✅ Editar calificaciones (solo si el período está activo)
- ✅ Escala 0-10 (aprobado >= 6)

### Alumno
- ✅ Dashboard con promedio y estadísticas
- ✅ Mis Calificaciones (historial completo)
- ✅ Mis Pagos (notas de remisión)
- ✅ Requisitos de Titulación (prácticas profesionales)

## 🕒 Lógica de Calificaciones

### Escala
- **0-10** (mínimo 6 para aprobar)
- Aprobado: >= 6
- Reprobado: < 6

### Jerarquía de Calificación Final
1. **Extra 2** (tiene prioridad máxima)
2. **Extra 1** (recuperación/ordinario)
3. **Calificación Final** (ordinaria)

### Control de Edición (Profesores)
- Las asignaciones tienen `fecha_inicio` y `fecha_fin`
- Los profesores solo pueden editar dentro del rango de fechas
- Pasado ese período, las calificaciones se bloquean automáticamente

## 🔧 API Endpoints

### Auth
- `POST /api/auth/login` - Login (admin/alumno/profesor)
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token

### Admin
- `GET/POST /api/alumnos` - Listar/Crear alumnos
- `PUT/DELETE /api/alumnos/:id` - Editar/Eliminar
- `GET/POST /api/profesores` - Profesores
- `GET/POST /api/carreras` - Carreras
- `GET/POST /api/materias` - Materias (paginado)
- `GET/POST /api/grupos` - Grupos
- `GET/POST /api/asignaciones` - Asignaciones
- `GET/PUT /api/calificaciones/*` - Calificaciones
- `GET/POST /api/pagos` - Pagos
- `GET/POST /api/practicas` - Prácticas profesionales
- `GET/POST /api/export` - Exportar

### Profesor
- `GET /api/profesor/mis-asignaciones` - Mis asignaciones
- `GET/PUT /api/profesor/asignacion/:id/calificaciones` - Editar calificaciones

### Alumno
- `GET /api/alumnos/:id` - Mis datos
- `GET /api/calificaciones/alumno/:id` - Mis calificaciones
- `GET /api/pagos/alumnos/:id` - Mis pagos

## 🐳 Docker

### Comandos Útiles
```bash
# Iniciar
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reconstruir solo un servicio
docker-compose up -d --build backend
docker-compose up -d --build frontend

# Eliminar volúmenes (CUIDADO: borra la DB)
docker-compose down -v
```

### Estructura Docker
- **Backend**: Python 3.10 + Flask en puerto 5000
- **Frontend**: Node 18 + Vite dev mode en puerto 3000
- **Red**: `portal-network` (bridge)
- **Volúmenes**: `.db` persistente, código en vivo

## 📝 Notas de Desarrollo

### Características Implementadas
- ✅ Autenticación JWT con 3 roles
- ✅ Relación uno a uno: Alumno ↔ Requisitos de titulación
- ✅ Relación uno a muchos: Alumno ↔ Prácticas profesionales
- ✅ Filtrado de materias por carrera en asignaciones
- ✅ Filtrado de alumnos por carrera en grupos
- ✅ Paginación en Materias (50 por página)
- ✅ Contraseñas hasheadas con bcrypt
- ✅ Validación de edición por fechas (asignaciones)
- ✅ Campos extra 1 y 2 en calificaciones
- ✅ Buscador de alumnos en Requisitos
- ✅ Formularios inline (sin modales)
- ✅ Sidebar adaptativo por rol

### Pendientes Sugeridos
- [ ] Implementar servicio social en requisitos
- [ ] Examen de idiomas (inglés)
- [ ] Subida de documentos (PDF)
- [ ] Notificaciones en tiempo real
- [ ] Migrar de SQLite a PostgreSQL para producción
- [ ] Tests automatizados

## 📄 Licencia

Proyecto desarrollado para la Universidad Felipe Villanueva.

---

**Desarrollado con ❤️ usando React, Flask y Docker**
