# SPEC: Portal de Calificaciones - Universidad Felipe Villanueva

**Versión:** 1.0  
**Fecha:** 2026-03-25  
**Stack:** Flask + React + SQLite (→ MySQL)  
**Diseño:** Moderno Gradiente (Turquoise + Glassmorphism)

---

## 1. Concepto & Visión

Portal académico para que los alumnos de la Universidad Felipe Villanueva consulten sus calificaciones, asistencia y estado de pagos. Los administradores gestionan todo el sistema. La experiencia visual es moderna, juvenil y colorida — refleja la energía de la institución con gradientes turquoise-verde y glassmorphism.

---

## 2. Paleta de Colores

| Rol | Color | Hex |
|-----|-------|-----|
| Primary (Turquesa) | `#008a8a` | Botones principales, navbar |
| Primary Dark | `#006666` | Hover states, headers |
| Accent (Verde brillante) | `#00d084` | Éxito, badges, highlights |
| Accent Light | `#4aeadc` | Gradientes, decorations |
| Background | `#f0fdfa` | Fondo de página |
| Card Background | `rgba(255,255,255,0.8)` | Cards con glassmorphism |
| Text Primary | `#1e293b` | Títulos, texto principal |
| Text Secondary | `#64748b` | Subtítulos, descripciones |
| Danger | `#ef4444` | Errores, delete |
| Warning | `#f59e0b` | Alertas |

---

## 3. Tipografía

- **Headings:** Inter (700, 600) — Google Fonts
- **Body:** Inter (400, 500)
- **Monospace:** JetBrains Mono (código SQL)

---

## 4. Arquitectura del Sistema

### Backend (Flask)
```
backend/
├── app.py                 # App principal + rutas auth
├── config.py              # Configuración (SQLite → MySQL)
├── models.py              # Modelos SQLAlchemy
├── routes/
│   ├── auth.py            # Login, logout, register
│   ├── alumnos.py         # CRUD alumnos
│   ├── carreras.py        # CRUD carreras
│   ├── materias.py        # CRUD materias
│   ├── calificaciones.py  # Calificaciones y asistencia
│   ├── pagos.py           # Notas de remisión
│   └── export.py          # Exportar SQL/Excel
├── utils/
│   ├── decorators.py      # @login_required, @admin_required
│   ├── export.py          # Generar SQL dump, Excel
│   └── security.py        # Bcrypt, JWT
├── migrations/            # Migraciones de base de datos
├── instance/
│   └── portal.db          # SQLite (local)
└── requirements.txt
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── api/               # Llamadas al backend
│   ├── components/
│   │   ├── layout/        # Navbar, Sidebar, Footer
│   │   ├── ui/            # Button, Input, Card, Modal
│   │   └── features/      # Components específicos
│   ├── pages/
│   │   ├── auth/          # Login, Register
│   │   ├── admin/         # Dashboard admin
│   │   └── alumno/        # Portal alumno
│   ├── hooks/             # Custom hooks
│   ├── context/           # Auth context
│   └── styles/
│       └── globals.css    # Tailwind + custom
├── public/
│   └── logo.png
├── index.html
├── tailwind.config.js
├── vite.config.js
└── package.json
```

---

## 5. Modelo de Datos

### Entidades Principales

```
Admin
├── id (PK)
├── username (unique)
├── email (unique)
├── password_hash
├── nombre
├── created_at
└── updated_at

Carrera
├── id (PK)
├── nombre
├── codigo (unique)
├── descripcion
├── activa (bool)
└── created_at

Materia
├── id (PK)
├── carrera_id (FK → Carrera)
├── nombre
├── codigo
├── creditos
└── created_at

Alumno
├── id (PK)
├── numero_control (unique)
├── nombre
├── apellido_paterno
├── apellido_materno
├── email (unique)
├── password_hash
├── carrera_id (FK → Carrera)
├── activo (bool)
├── fecha_registro
└── created_at

Calificacion
├── id (PK)
├── alumno_id (FK → Alumno)
├── materia_id (FK → Materia)
├── asistencia_1 a asistencia_5 (int 0-1)
├── practica_1 (decimal 0-20)
├── practica_2 (decimal 0-20)
├── calificacion_final (decimal 0-20)
├── periodo
├── anio
└── created_at

PracticaProfesional
├── id (PK)
├── alumno_id (FK → Alumno)
├── numero_practica (1 o 2)
├── nombre_empresa
├── fecha_inicio
├── fecha_fin
├── reporte_entregado (bool)
├── validada (bool)
├── observaciones
└── created_at

NotaRemision
├── id (PK)
├── alumno_id (FK → Alumno)
├── concepto
├── monto (decimal)
├── fecha_emision
├── pagada (bool)
├── fecha_pago
├── created_by (FK → Admin)
└── created_at
```

---

## 6. Endpoints API

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Login admin/alumno |
| POST | `/api/auth/register` | Registro alumno (desde /signup) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Usuario actual |

### Alumnos
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/alumnos` | Listar alumnos (admin) |
| POST | `/api/alumnos` | Crear alumno (admin) |
| GET | `/api/alumnos/<id>` | Ver alumno |
| PUT | `/api/alumnos/<id>` | Editar alumno (admin) |
| DELETE | `/api/alumnos/<id>` | Eliminar alumno (admin) |
| GET | `/api/alumnos/mis-datos` | Mis datos (alumno logueado) |

### Carreras
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/carreras` | Listar carreras |
| POST | `/api/carreras` | Crear carrera (admin) |
| GET | `/api/carreras/<id>/materias` | Materias de una carrera |

### Materias
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/materias` | Listar materias |
| POST | `/api/materias` | Crear materia (admin) |
| GET | `/api/materias/<id>` | Ver materia |

### Calificaciones
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/alumnos/<id>/calificaciones` | Todas las calificaciones de un alumno |
| POST | `/api/calificaciones` | Crear/actualizar calificación (admin) |
| GET | `/api/alumnos/<id>/historial` | Historial completo (alumno) |

### Prácticas
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/alumnos/<id>/practicas` | Prácticas de un alumno |
| POST | `/api/practicas` | Crear práctica (admin) |
| PUT | `/api/practicas/<id>` | Validar práctica (admin) |

### Pagos
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/alumnos/<id>/pagos` | Notas de remisión de un alumno |
| POST | `/api/pagos` | Crear nota (admin) |
| PUT | `/api/pagos/<id>` | Marcar pagada/no pagada (admin) |

### Exportación
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/export/sql` | Descargar dump SQL completo |
| GET | `/api/export/excel` | Descargar datos en Excel |

---

## 7. Diseño de Pantallas

### 7.1 Login (`/login`)
- Logo centrado arriba
- Formulario: email + contraseña
- Botón "Iniciar Sesión" gradient turquoise
- Link "¿Olvidaste tu contraseña?" (placeholder)
- Fondo con gradiente sutil

### 7.2 Registro Alumno (`/signup`)
- Título: "Registro de Alumno"
- Campos: nombre, apellido, email, número de control, contraseña, confirmar contraseña
- Nota: "Este link es privado. Solo alumnos autorizados."
- Botón "Registrarse"
- Link a login

### 7.3 Dashboard Admin (`/admin`)
- **Navbar superior:** Logo izquierda, nombre admin derecha, logout
- **Sidebar izquierdo:** Iconos + texto para cada sección
  - Dashboard (ícono casita)
  - Alumnos (ícono usuarios)
  - Carreras (ícono libro)
  - Materias (ícono carpeta)
  - Calificaciones (ícono nota)
  - Pagos (ícono dinero)
  - Exportar (ícono descarga)
  - Configuración (ícono engranaje)
- **Contenido principal:** Cards con gradiente glassmorphism
- **Tabs/Fichas:** Como propuso el usuario, acceso rápido a secciones

### 7.4 Portal Alumno (`/alumno`)
- **Navbar:** Logo, nombre alumno, cerrar sesión
- **Cards:**
  - Mis Calificaciones (link a detalle)
  - Mis Pagos (estado de cuenta)
  - Requisitos de Titulación (prácticas profesionales)
  - Mis Datos

### 7.5 Detalle Calificaciones Alumno
- Tabla con materias, asistencia (5), prácticas (2), cal final
- Color verde si ≥13, rojo si <13, gris si vacío
- Período y año selector

### 7.6 Requisitos de Titulación
- Card "Práctica Profesional 1" (completada/no)
- Card "Práctica Profesional 2" (completada/no)
- Detalle: empresa, fechas, estado de validación

### 7.7 Gestión Pagos (Admin)
- Tabla de notas de remisión
- Filtro: alumno, status (pagada/pendiente)
- Botón "Nueva Nota"
- Toggle rápido: marcar como pagada/no pagada

### 7.8 Exportación (Admin)
- Card con botón "Descargar SQL"
- Card con botón "Descargar Excel"
- Lista de tablas disponibles para exportar

---

## 8. Seguridad

### Contraseñas
- Bcrypt con salt rounds = 12
- Nunca almacenar contraseñas en texto plano

### Autenticación
- JWT (JSON Web Tokens) para sesiones
- Token en httpOnly cookie
- Refresh token para sesiones largas
- Expiración: 24 horas

### Autorización
- Admin: acceso total a todas las rutas `/api/admin/*`
- Alumno: solo sus propios datos en `/api/alumnos/*`
- Decoradores: `@login_required`, `@admin_required`

### Validación de Entrada
- Validación en backend (no confiar en frontend)
- Sanitización de inputs
- Prepared statements para SQL (SQLAlchemy ORM)

### Headers de Seguridad
- CORS configurado para dominio específico
- Helmet.js para headers de seguridad
- Rate limiting en login (prevenir brute force)

---

## 9. Migración SQLite → MySQL

### Preparación (Ya implementada)
- SQLAlchemy como ORM (abstracto de base de datos)
- Configuración por entorno (`development` / `production`)

### Cambio de URI
```python
# development (SQLite)
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/portal.db'

# production (MySQL)
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@host:3306/portal_db'
```

### Pasos de Migración
1. Exportar datos desde SQLite (`/api/export/sql`)
2. Crear base de datos en MySQL
3. Importar dump SQL
4. Cambiar URI en config
5. Reiniciar aplicación

---

## 10. Screens Principales (Mockup)

### Login
```
┌─────────────────────────────────┐
│         [LOGO]                 │
│                                 │
│    Portal de Calificaciones     │
│      Universidad FV             │
│                                 │
│  ┌─────────────────────────┐    │
│  │  Email                 │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Contraseña             │    │
│  └─────────────────────────┘    │
│                                 │
│  [   Iniciar Sesión   ] (grad)  │
│                                 │
│   ¿Olvidaste tu contraseña?     │
└─────────────────────────────────┘
```

### Dashboard Admin
```
┌──────┬──────────────────────────────┐
│      │  🔔 Bienvenido, Admin    [👤] │
│ 📊   ├──────────────────────────────┤
│ ──── │                              │
│ 👥   │  ┌────────┐ ┌────────┐      │
│ ──── │  │Alumnos │ │Carreras│      │
│ 📚   │  │  156   │ │   12   │      │
│ ──── │  └────────┘ └────────┘      │
│ 📝   │                              │
│ ──── │  ┌────────┐ ┌────────┐      │
│ 💰   │  │Pagos   │ │Exportar│      │
│ ──── │  │Pend: 8 │ │  SQL   │      │
│ 📥   │  └────────┘ └────────┘      │
│      │                              │
└──────┴──────────────────────────────┘
```

### Portal Alumno
```
┌─────────────────────────────────┐
│  [LOGO]  Juan Pérez    [🚪]     │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────┐    │
│  │ 📝 Mis Calificaciones    │    │
│  │ Ver historial completo   │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 💳 Mis Pagos            │    │
│  │ 2 pendientes de pago     │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 🎓 Requisitos Titulación │    │
│  │ Práctica 1 ✓  Práctica 2 │    │
│  └─────────────────────────┘    │
│                                 │
└─────────────────────────────────┘
```

---

## 11. Dependencias

### Backend
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-Migrate==4.0.5
bcrypt==4.1.2
python-dotenv==1.0.0
Werkzeug==3.0.1
PyMySQL==1.1.0
openpyxl==3.1.2
```

### Frontend
```
react==18.2.0
react-dom==18.2.0
react-router-dom==6.22.0
axios==1.6.7
tailwindcss==3.4.1
@headlessui/react==1.7.18
lucide-react==0.344.0
vite==5.1.4
```

---

## 12. Funcionalidades por Fase

### Fase 1: Fundamentos
- [x] Spec y diseño
- [ ] Setup proyecto (Flask + React)
- [ ] Modelos de datos
- [ ] Auth básico (login/logout)
- [ ] CRUD Carreras

### Fase 2: Gestión
- [ ] CRUD Materias
- [ ] CRUD Alumnos
- [ ] Asignar alumno a carrera

### Fase 3: Calificaciones
- [ ] Ingresar calificaciones (admin)
- [ ] Ver calificaciones (alumno)
- [ ] Prácticas profesionales

### Fase 4: Pagos y Exportación
- [ ] Notas de remisión
- [ ] Exportar SQL
- [ ] Exportar Excel

### Fase 5: Polish
- [ ] UI/UX final
- [ ] Tests
- [ ] Documentación
- [ ] Deploy的准备

---

*Documento creado el 25 de marzo de 2026*
