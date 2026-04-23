# Portal FV Frontend

Frontend del Portal de Calificaciones de la Universidad Felipe Villanueva.

## Requisitos

- Node.js 18+
- npm o yarn

## Instalación

```bash
# Instalar dependencias
npm install

# Crear archivo de entorno
cp .env.example .env
```

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
VITE_API_URL=http://localhost:5000/api
```

## Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# El frontend estará disponible en http://localhost:3000
# El backend (Flask) debe estar corriendo en http://localhost:5000
```

## Build

```bash
# Crear build de producción
npm run build

# Previsualizar build
npm run preview
```

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── api/           # Llamadas al backend
│   ├── components/    # Componentes reutilizables
│   │   ├── layout/    # Layout principal (Navbar, Sidebar)
│   │   └── ui/        # Componentes UI (Button, Card, Modal...)
│   ├── pages/         # Páginas de la aplicación
│   │   ├── auth/      # Login, Register
│   │   ├── admin/     # Panel de administración
│   │   └── alumno/    # Portal del alumno
│   ├── hooks/         # Custom hooks
│   ├── context/       # Contextos (Auth)
│   └── index.css      # Estilos globales + Tailwind
├── public/            # Archivos estáticos
├── tailwind.config.js # Configuración de Tailwind
└── vite.config.js     # Configuración de Vite
```

## Rutas

### Auth
- `/login` - Inicio de sesión
- `/signup` - Registro de alumnos

### Admin
- `/admin` - Dashboard
- `/admin/alumnos` - Gestión de alumnos
- `/admin/carreras` - Gestión de carreras
- `/admin/materias` - Gestión de materias
- `/admin/calificaciones` - Gestión de calificaciones
- `/admin/pagos` - Gestión de pagos
- `/admin/exportar` - Exportar datos

### Alumno
- `/alumno` - Dashboard
- `/alumno/calificaciones` - Ver calificaciones
- `/alumno/pagos` - Ver pagos
- `/alumno/requisitos` - Requisitos de titulación

## Tecnologías

- React 18
- React Router 6
- Tailwind CSS
- Axios
- Lucide Icons
- Vite

## Diseño

El proyecto utiliza un diseño moderno con:

- **Glassmorphism**: Efectos de cristal con blur y transparencias
- **Gradientes**: Turquoise (#008a8a) a Verde (#00d084)
- **Responsive**: Adaptable a móviles y escritorio
