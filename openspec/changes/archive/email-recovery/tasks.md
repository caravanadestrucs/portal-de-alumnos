# Tasks: Sistema de Email y Recuperación de Contraseña

**Change:** `email-recovery`
**Status:** Draft
**Created:** 2026-06-19
**Fases:** 5 | **Tareas:** 18

---

## Fase 1: Backend Infrastructure

Construye los cimientos del sistema: modelo de configuración, utilidad de email, utilidad de tokens JWT, y el blueprint de settings.

### TASK-EMAIL-1.1 — Modelo `Config` en `models.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-1.1 |
| **Descripción** | Agregar el modelo SQLAlchemy `Config` con esquema key-value para almacenar configuración del sistema (SMTP, personalización, etc.). |
| **Archivos** | `backend/models.py` |
| **Dependencias** | — |

#### Acceptance Criteria

1. Modelo `Config` con tabla `config` y campos:
   - `id` — Integer, primary key
   - `key` — String(100), unique, not null
   - `value` — Text, nullable (permite valores vacíos)
   - `updated_at` — DateTime, default `datetime.utcnow`, onupdate `datetime.utcnow`
2. Método `to_dict()` que retorna `{ id, key, value, updated_at }`
3. `unique=True` en `key` — cualquier intento de duplicado lanza `IntegrityError`
4. `nullable=False` en `key` — valores vacíos o `None` fallan a nivel DB
5. Posicionar el modelo al inicio del archivo, después de los imports, con comentario `# ============================================================` arriba y abajo

---

### TASK-EMAIL-1.2 — Utilidad de Email `utils/email.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-1.2 |
| **Descripción** | Crear el módulo `backend/utils/email.py` con la función `send_email()` que usa `smtplib` de la stdlib para enviar correos HTML. Lee la configuración SMTP desde el modelo `Config` en DB. |
| **Archivos** | `backend/utils/email.py` (**NUEVO**) |
| **Dependencias** | TASK-EMAIL-1.1 |

#### Acceptance Criteria

1. Función `send_email(to_email: str, subject: str, html_body: str) -> dict`:
   - Lee `Config.query.all()` y construye dict con claves `smtp_*`
   - Si falta `smtp_host` o `smtp_email` → retorna `{ "success": False, "error": "SMTP no configurado" }`
   - Conecta vía `smtplib.SMTP(host, port, timeout=10)`
   - Si `smtp_use_tls == "true"` → llama `starttls()`
   - Autentica con `smtp_email` / `smtp_password`
   - Construye `MIMEText(html_body, 'html')` con headers `Subject`, `From`, `To`
   - Envía con `send_message(msg)`
   - Cierra conexión con `quit()`
   - Retorna `{ "success": True }` en éxito
2. Manejo de errores: **nunca lanza excepción**, siempre retorna dict con `success: False` y mensaje de error genérico (loggea el detalle con `app.logger.error`)
3. Sin dependencias externas — solo `smtplib`, `email.mime.text.MIMEText`, `logging`
4. Encoding UTF-8 en el mensaje
5. Docstring completo con Args/Returns

---

### TASK-EMAIL-1.3 — Token Functions en `utils/security.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-1.3 |
| **Descripción** | Agregar `generate_reset_token(email, role)` y `verify_reset_token(token)` a `utils/security.py`. Usan `flask_jwt_extended` con la misma `JWT_SECRET_KEY` de la app. |
| **Archivos** | `backend/utils/security.py` |
| **Dependencias** | — |

#### Acceptance Criteria

1. `generate_reset_token(email: str, role: str) -> str`:
   - Llama `create_access_token(identity=email, additional_claims={...}, expires_delta=timedelta(minutes=15))`
   - Claims adicionales: `{ "purpose": "password_reset", "email": email, "role": role }`
   - Expira exactamente 15 minutos después de `iat`
   - Retorna el JWT string firmado

2. `verify_reset_token(token: str) -> dict | None`:
   - Llama `decode_token(token)`
   - Verifica `purpose == "password_reset"`
   - Retorna `{ "email": ..., "role": ... }` si es válido
   - Retorna `None` si: expiró, firma inválida, malformado, o `purpose` incorrecto
   - Usa `try/except` capturando `Exception` genérico

3. Ambas funciones con docstring, type hints, y ubicadas después de las funciones existentes con comentario separador

---

### TASK-EMAIL-1.4 — Blueprint `routes/settings.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-1.4 |
| **Descripción** | Crear el blueprint `settings_bp` en `backend/routes/settings.py` con endpoints CRUD para configuración SMTP más test de email. Registrado con prefijo `/api/config`. |
| **Archivos** | `backend/routes/settings.py` (**NUEVO**) |
| **Dependencias** | TASK-EMAIL-1.1, TASK-EMAIL-1.2 |

#### Acceptance Criteria

1. **Estructura**: Blueprint `settings_bp = Blueprint('settings', __name__)`

2. **`GET /api/config`** (`@admin_required`):
   - Lee `Config.query.all()` y construye objeto `{ key: value }`
   - `smtp_password` se retorna como `"****"` (enmascarado) si tiene valor
   - Si no hay configuraciones, retorna `{}`
   - Respuesta `200`: `{ "config": { "smtp_host": "...", ... } }`

3. **`PUT /api/config`** (`@admin_required`):
   - Recibe body con pares key-value a actualizar
   - Valida que todas las keys del body existan en la tabla `Config` (consulta `Config.query.all()` para obtener keys válidas)
   - **Validación SMTP** (cuando se envían campos SMTP):
     - `smtp_host`: no vacío
     - `smtp_port`: entero entre 1 y 65535
     - `smtp_email`: formato email válido (reutilizar `validate_email`)
     - `smtp_password`: no vacío
     - `smtp_use_tls`: booleano convertible
   - Si validación falla → `400` con mensaje descriptivo
   - Actualiza SOLO las keys enviadas (las no incluidas quedan intactas)
   - Si `smtp_password` está presente, se guarda como texto plano
   - Respuesta `200`: `{ "message": "Configuración actualizada", "config": { ... } }`
   - Si `smtp_password` NO fue incluido, en la respuesta se retorna enmascarado
   - Rate limit: `@limiter.limit("30/hour")`

4. **`POST /api/config/test`** (`@admin_required`):
   - Obtiene el email del admin desde el JWT (`claims.get('email')` o de `Admin.query.get(claims['id']).email`)
   - Lee la configuración SMTP actual de DB
   - Si SMTP incompleto → `400` con mensaje
   - Llama `send_email(admin_email, "Prueba SMTP - Portal FV", "<html>...")`
   - Si éxito → `200` con `{ "message": "Email de prueba enviado exitosamente" }`
   - Si error SMTP → `502` con `{ "error": "Error al enviar email de prueba", "details": "..." }`
   - Rate limit: `@limiter.limit("10/hour")`

---

## Fase 2: Backend Auth Endpoints

Implementa los endpoints de autenticación para recuperación de contraseña.

### TASK-EMAIL-2.1 — Helper `_find_user_by_email` en `auth.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-2.1 |
| **Descripción** | Agregar función auxiliar privada `_find_user_by_email(email)` que busca secuencialmente en las 3 tablas (Admin → Profesor → Alumno) y retorna el usuario y su tipo. |
| **Archivos** | `backend/routes/auth.py` |
| **Dependencias** | — |

#### Acceptance Criteria

1. Función `_find_user_by_email(email: str) -> tuple`:
   - Busca `Admin.query.filter_by(email=email).first()` → si existe, retorna `(admin, 'admin')`
   - Si no, busca `Profesor.query.filter_by(email=email).first()` → retorna `(profesor, 'profesor')`
   - Si no, busca `Alumno.query.filter_by(email=email).first()` → retorna `(alumno, 'alumno')`
   - Si no encuentra en ninguna → retorna `(None, None)`
2. Ubicar como función privada al inicio del archivo, después de los imports y antes de los endpoints
3. Incluir docstring explicativo

---

### TASK-EMAIL-2.2 — Endpoint `POST /api/auth/forgot-password`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-2.2 |
| **Descripción** | Endpoint público que recibe `{ "email" }`, busca el email en las 3 tablas, genera un JWT reset token de 15 min, y envía un email con el link de recuperación. **Siempre retorna 200**. |
| **Archivos** | `backend/routes/auth.py` |
| **Dependencias** | TASK-EMAIL-2.1, TASK-EMAIL-1.3, TASK-EMAIL-1.2 |

#### Acceptance Criteria

1. **Ruta**: `POST /forgot-password` (dentro de `auth_bp` → `/api/auth/forgot-password`)
2. **Body**: `{ "email": "..." }`
3. **Validación**: email no vacío, formato válido (reutilizar `validate_email`)
4. **Auth**: pública (sin `@jwt_required`)
5. **Rate limit**: `@limiter.limit("5/hour")`
6. **Flujo cuando email existe**:
   - Llama `_find_user_by_email(email)` → obtiene `(user, role)`
   - Genera token: `generate_reset_token(email, role)`
   - Construye URL: `{FRONTEND_URL}/reset-password?token={token}` (FRONTEND_URL de `os.environ.get('FRONTEND_URL', 'http://localhost:5173')`)
   - Crea HTML body usando `render_reset_email(reset_url)` (función inline o importada)
   - Envía: `send_email(email, "Recuperación de Contraseña", html)`
   - Loggea resultado del envío
7. **Flujo cuando email NO existe**:
   - Simplemente loggea `"Solicitud de recuperación para email no registrado: {email}"`
   - **No** envía email
   - **No** retorna error
8. **Siempre retorna `200`**: `{ "message": "Si el email está registrado, recibirás un enlace de recuperación en tu bandeja de entrada" }`
9. **HTML Email Template**: Función `render_reset_email(reset_url: str) -> str` que genera HTML inline:
   - Encabezado: "Recuperación de Contraseña"
   - Logo universidad (URL desde Config `app_logo_url` o placeholder)
   - Párrafo informativo
   - Botón/link estilizado: `<a href="{reset_url}" style="...">Restablecer Contraseña</a>`
   - Texto: "Este enlace expira en 15 minutos"
   - Texto: "Si no solicitaste este cambio, ignora este mensaje"
   - Footer: "Universidad Felipe Villanueva"
   - Responsive, inline styles para compatibilidad con clientes email
10. **Timing constante**: No debe haber diferencia perceptible en tiempo de respuesta entre email existente y no existente (pequeño `time.sleep(0.1)` si es necesario)
11. **Manejo de errores SMTP**: Si `send_email` falla, se loggea el error pero se retorna `200` igual

---

### TASK-EMAIL-2.3 — Endpoint `POST /api/auth/reset-password`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-2.3 |
| **Descripción** | Endpoint público que recibe `{ "token", "password" }`, verifica el JWT reset token, busca al usuario en la tabla correspondiente, y actualiza su `password_hash`. |
| **Archivos** | `backend/routes/auth.py` |
| **Dependencias** | TASK-EMAIL-2.1, TASK-EMAIL-1.3 |

#### Acceptance Criteria

1. **Ruta**: `POST /reset-password` (dentro de `auth_bp` → `/api/auth/reset-password`)
2. **Body**: `{ "token": "<jwt>", "password": "nueva-pass-123" }`
3. **Auth**: pública (sin `@jwt_required`, la auth es vía el reset token)
4. **Rate limit**: `@limiter.limit("10/hour")`
5. **Validaciones**:
   - `password` presente y >= 6 caracteres → si falla, `400` con `"La contraseña debe tener al menos 6 caracteres"`
   - `token` presente → si falta, `400` con `"Token requerido"`
6. **Flujo principal**:
   - Llama `verify_reset_token(token)`
   - Si retorna `None` → `400` con `{ "error": "Token inválido o expirado" }`
   - Extrae `email` y `role` del diccionario retornado
   - Según `role`:
     - `"admin"` → `Admin.query.filter_by(email=email).first()`
     - `"profesor"` → `Profesor.query.filter_by(email=email).first()`
     - `"alumno"` → `Alumno.query.filter_by(email=email).first()`
   - Si usuario no existe → `400` con `{ "error": "Usuario no encontrado" }`
   - Llama `user.set_password(password)`
   - `db.session.commit()`
   - Retorna `200` con `{ "message": "Contraseña actualizada exitosamente" }`
7. **Manejo de errores**: `try/except` con `rollback()` y retorno `500`
8. Ubicar después del endpoint `forgot-password`

---

### TASK-EMAIL-2.4 — Registrar Blueprint y Seed en `app.py`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-2.4 |
| **Descripción** | Registrar el blueprint `settings_bp` en la app Flask. Agregar seed de configuración por defecto en el bloque `with app.app_context()` después de `db.create_all()`. |
| **Archivos** | `backend/app.py` |
| **Dependencias** | TASK-EMAIL-1.4 |

#### Acceptance Criteria

1. **Import**: `from routes.settings import settings_bp` (agregar junto a los demás imports de blueprints, en orden alfabético o al final)
2. **Registro**: `app.register_blueprint(settings_bp, url_prefix='/api/config')` (agregar después de los registros existentes)
3. **Seed de Config**: Dentro del bloque `with app.app_context():`, después de `db.create_all()`, antes o después del seed de Admin:
   ```python
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
   ```
4. Loggear con `print('[OK] Configuración por defecto creada')` después del seed

---

## Fase 3: Frontend API

Conecta el frontend con los nuevos endpoints del backend.

### TASK-EMAIL-3.1 — Funciones `forgotPassword` / `resetPassword` en `api/auth.js`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-3.1 |
| **Descripción** | Agregar dos funciones API exportables en `frontend/src/api/auth.js` para los endpoints de recuperación de contraseña. |
| **Archivos** | `frontend/src/api/auth.js` |
| **Dependencias** | — |

#### Acceptance Criteria

1. `forgotPassword(email)`:
   - Llama `api.post('/auth/forgot-password', { email })`
   - Retorna `response.data`

2. `resetPassword(token, password)`:
   - Llama `api.post('/auth/reset-password', { token, password })`
   - Retorna `response.data`

3. Ambas funciones exportadas con `export const`
4. Mantener el mismo patrón de las funciones existentes (async/await, sin try/catch — el error se maneja en el componente)

---

### TASK-EMAIL-3.2 — Módulo API `api/settings.js`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-3.2 |
| **Descripción** | Crear el módulo `frontend/src/api/settings.js` con funciones para los endpoints de configuración SMTP. |
| **Archivos** | `frontend/src/api/settings.js` (**NUEVO**) |
| **Dependencias** | — |

#### Acceptance Criteria

1. Importa `api` desde `./index` (como los demás API modules)
2. `getSettings()`:
   - Llama `api.get('/config')`
   - Retorna `response.data`

3. `updateSettings(data)`:
   - Recibe un objeto con los pares key-value a actualizar
   - Llama `api.put('/config', data)`
   - Retorna `response.data`

4. `testEmail()`:
   - Llama `api.post('/config/test')`
   - Retorna `response.data`

5. Todas exportadas con `export const`
6. Patrón async/await consistente con el resto del proyecto

---

## Fase 4: Frontend Pages

Crea las páginas de recuperación de contraseña y configuración SMTP.

### TASK-EMAIL-4.1 — Página `ForgotPassword.jsx`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-4.1 |
| **Descripción** | Crear la página `/forgot-password` con formulario de email para solicitar recuperación de contraseña. Siempre muestra el mismo mensaje de éxito (seguridad por obscuridad). |
| **Archivos** | `frontend/src/pages/auth/ForgotPassword.jsx` (**NUEVO**) |
| **Dependencias** | TASK-EMAIL-3.1 |

#### Acceptance Criteria

1. **Ruta**: `/forgot-password` (la ruta se configura en App.jsx — TASK-EMAIL-5.2)
2. **Layout**: público, mismo estilo que `Login.jsx` (fondo gradient, card glass, logo)
3. **Componentes**: reutilizar `Input` y `Button` de `components/ui/`
4. **Estados**:
   - `email` (string)
   - `loading` (bool)
   - `submitted` (bool) — para mostrar mensaje de éxito
   - `error` (string) — para errores de validación local
5. **Validación cliente** (antes de enviar):
   - Email vacío → `"El email es requerido"`
   - Email con formato inválido → `"Formato de email inválido"`
6. **Al submit**:
   - Setea `loading = true`
   - Llama `forgotPassword(email)`
   - **Siempre** setea `submitted = true` (incluso si hay error de red — para no revelar nada)
   - Si hay error de red, se loggea en consola pero se muestra el mismo mensaje de éxito
7. **Estado `submitted === true`**: Muestra mensaje de éxito:
   - "Si el email está registrado, recibirás un enlace de recuperación en tu bandeja de entrada"
   - Icono de check / sobre
   - Link "Volver al inicio de sesión" → `/login`
   - Ocultar el formulario
8. **Estado normal**: Formulario con:
   - Título: "Recuperar Contraseña"
   - Subtítulo: "Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña"
   - Input de email con icono `Mail`
   - Botón: "Enviar enlace de recuperación"
   - Link: "Volver al inicio de sesión" → `/login`

---

### TASK-EMAIL-4.2 — Página `ResetPassword.jsx`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-4.2 |
| **Descripción** | Crear la página `/reset-password` con formulario de nueva contraseña. Lee el token del query string, valida contraseñas, y llama al endpoint de reset. |
| **Archivos** | `frontend/src/pages/auth/ResetPassword.jsx` (**NUEVO**) |
| **Dependencias** | TASK-EMAIL-3.1 |

#### Acceptance Criteria

1. **Ruta**: `/reset-password?token=xxx` (lee `token` de `useSearchParams` o `useParams`)
2. **Layout**: público, mismo estilo que `Login.jsx`
3. **Componentes**: reutilizar `Input` y `Button`
4. **Estados**:
   - `password` (string)
   - `confirmPassword` (string)
   - `loading` (bool)
   - `error` (string)
   - `success` (bool)
5. **Validación cliente**:
   - Token ausente → mostrar mensaje `"Token de recuperación no encontrado"` con link a `/forgot-password`
   - Password < 6 caracteres → `"La contraseña debe tener al menos 6 caracteres"`
   - Passwords no coinciden → `"Las contraseñas no coinciden"`
6. **Al submit exitoso**:
   - `success = true`
   - Muestra: "Contraseña actualizada exitosamente. Ahora puedes iniciar sesión."
   - Botón "Ir a Iniciar Sesión" → `/login`
7. **En caso de error del backend**:
   - Muestra error (ej: "El link de recuperación es inválido o ha expirado")
   - Link "Solicitar nuevo link" → `/forgot-password`
8. **Estados visuales**: loading en botón durante submit, disabled mientras carga

---

### TASK-EMAIL-4.3 — Página `Settings.jsx` (Admin SMTP Config)

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-4.3 |
| **Descripción** | Crear la página `/admin/configuracion` dentro del panel de administración con formulario para configurar parámetros SMTP, más botón de prueba de email. |
| **Archivos** | `frontend/src/pages/admin/Settings.jsx` (**NUEVO**) |
| **Dependencias** | TASK-EMAIL-3.2 |

#### Acceptance Criteria

1. **Ruta**: `/admin/configuracion` (ruta anidada bajo el layout de admin — se configura en App.jsx)
2. **Layout**: admin (hereda el Layout con Sidebar vía las rutas anidadas en App.jsx)
3. **Componentes**: reutilizar `Input`, `Button`, `Card` de `components/ui/`
4. **Estados**:
   - `formData` — objeto con `{ smtp_host, smtp_port, smtp_email, smtp_password, smtp_use_tls, app_name, app_logo_url }`
   - `loading` — carga inicial
   - `saving` — guardando configuración
   - `testing` — enviando email de prueba
   - `toast` — notificaciones de éxito/error
5. **Al montar (`useEffect`)**:
   - Llama `getSettings()`
   - Pre-carga campos `smtp_host`, `smtp_port`, `smtp_email`, `smtp_use_tls`, `app_name`, `app_logo_url`
   - `smtp_password` se deja vacío (por seguridad)
   - Manejo de error de carga con toast
6. **Formulario**:
   - **Sección SMTP**:
     - Host (text input)
     - Puerto (number input, placeholder 587)
     - Email (email input)
     - Password (password input, placeholder "••••••••" si hay valor guardado)
     - Usar TLS (checkbox, default checked)
   - **Sección Personalización** (colapsable o secundaria):
     - Nombre de la aplicación
     - URL del logo
   - Botón "Guardar configuración"
   - Botón "Enviar email de prueba"
7. **Validación cliente**:
   - Puerto debe ser número entre 1-65535
   - Host no vacío cuando se guarda
   - Email formato válido
8. **Guardar configuración**:
   - `saving = true`
   - Llama `updateSettings(formData)` — envía SOLO los campos que el usuario modificó (o todos, pero el backend solo actualiza los recibidos)
   - Si éxito → toast "Configuración guardada exitosamente"
   - Si error → toast con mensaje de error
   - Al recibir respuesta, actualiza `formData` con los valores del servidor (para reflejar cambios)
   - `smtp_password` siempre se deja vacío en el estado después de guardar
9. **Enviar email de prueba**:
   - `testing = true`
   - Llama `testEmail()`
   - Si éxito → toast "Email de prueba enviado exitosamente"
   - Si error → toast con mensaje de error del servidor
10. **Estados visuales**: loaders en botones durante operaciones, disabled mientras carga

---

## Fase 5: Frontend Integration

Integra las nuevas páginas en la navegación existente.

### TASK-EMAIL-5.1 — Link "¿Olvidaste tu contraseña?" en `Login.jsx`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-5.1 |
| **Descripción** | Agregar un link "¿Olvidaste tu contraseña?" debajo del botón de iniciar sesión y antes del link de registro. |
| **Archivos** | `frontend/src/pages/auth/Login.jsx` |
| **Dependencias** | — |

#### Acceptance Criteria

1. Link con texto "¿Olvidaste tu contraseña?" entre el botón de submit y el link de registro
2. Ruta: `/forgot-password`
3. Estilos consistentes con el link de registro existente: `text-sm text-primary-600 hover:text-primary-700 hover:underline`
4. Encerrado en un `div` con `className="mt-4 text-center"` para separación
5. Tamaño `text-sm` como el link de registro

---

### TASK-EMAIL-5.2 — Rutas en `App.jsx`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-5.2 |
| **Descripción** | Agregar las rutas públicas `/forgot-password`, `/reset-password` y la ruta admin `/admin/configuracion` en `App.jsx`. |
| **Archivos** | `frontend/src/App.jsx` |
| **Dependencias** | TASK-EMAIL-4.1, TASK-EMAIL-4.2, TASK-EMAIL-4.3 |

#### Acceptance Criteria

1. **Imports** nuevos:
   ```jsx
   import ForgotPassword from './pages/auth/ForgotPassword';
   import ResetPassword from './pages/auth/ResetPassword';
   import AdminSettings from './pages/admin/Settings';
   ```
2. **Rutas públicas** (dentro de `<Routes>`, después de `/signup`):
   ```jsx
   <Route path="/forgot-password" element={<PublicRoute><ForgotPassword /></PublicRoute>} />
   <Route path="/reset-password" element={<PublicRoute><ResetPassword /></PublicRoute>} />
   ```
3. **Ruta admin** (dentro de la ruta anidada de `/admin`, antes de `exportar` o al final):
   ```jsx
   <Route path="configuracion" element={<AdminSettings />} />
   ```
4. La ruta admin hereda el `Layout` con Sidebar del `ProtectedRoute` padre

---

### TASK-EMAIL-5.3 — Ítem "Configuración" en `Sidebar.jsx`

| Campo | Valor |
|-------|-------|
| **ID** | TASK-EMAIL-5.3 |
| **Descripción** | Agregar el ítem "Configuración" al array `adminNavItems` en `Sidebar.jsx`, en la última posición antes de "Exportar". |
| **Archivos** | `frontend/src/components/layout/Sidebar.jsx` |
| **Dependencias** | — |

#### Acceptance Criteria

1. Importar `Settings` de `lucide-react` (agregar al bloque de imports existente)
2. Agregar entrada en `adminNavItems` (antes del item de Exportar):
   ```jsx
   { path: '/admin/configuracion', icon: Settings, label: 'Configuración' },
   ```
3. El ítem es visible SOLO cuando el Sidebar renderiza `adminNavItems` (usuarios `type === 'admin'`)
4. Al hacer clic, navega a `/admin/configuracion`
5. Icono `Settings` de lucide-react (tamaño consistente: `size={20}`)

---

## Matriz de Trazabilidad

| Tarea | REQ Relacionados | Fase | Dependencias | Archivos |
|-------|------------------|------|--------------|----------|
| TASK-EMAIL-1.1 | REQ-EMAIL-001 | 1 | — | `models.py` |
| TASK-EMAIL-1.2 | REQ-EMAIL-015, REQ-EMAIL-016 | 1 | TASK-EMAIL-1.1 | `utils/email.py` (NUEVO) |
| TASK-EMAIL-1.3 | REQ-EMAIL-010 | 1 | — | `utils/security.py` |
| TASK-EMAIL-1.4 | REQ-EMAIL-002, REQ-EMAIL-003, REQ-EMAIL-004 | 1 | TASK-EMAIL-1.1, TASK-EMAIL-1.2 | `routes/settings.py` (NUEVO) |
| TASK-EMAIL-2.1 | REQ-EMAIL-009, REQ-EMAIL-012 | 2 | — | `routes/auth.py` |
| TASK-EMAIL-2.2 | REQ-EMAIL-009, REQ-EMAIL-013 | 2 | TASK-EMAIL-2.1, TASK-EMAIL-1.3, TASK-EMAIL-1.2 | `routes/auth.py` |
| TASK-EMAIL-2.3 | REQ-EMAIL-012 | 2 | TASK-EMAIL-2.1, TASK-EMAIL-1.3 | `routes/auth.py` |
| TASK-EMAIL-2.4 | REQ-EMAIL-019 | 2 | TASK-EMAIL-1.4 | `app.py` |
| TASK-EMAIL-3.1 | REQ-EMAIL-017 | 3 | — | `api/auth.js` |
| TASK-EMAIL-3.2 | REQ-EMAIL-018 | 3 | — | `api/settings.js` (NUEVO) |
| TASK-EMAIL-4.1 | REQ-EMAIL-008 | 4 | TASK-EMAIL-3.1 | `ForgotPassword.jsx` (NUEVO) |
| TASK-EMAIL-4.2 | REQ-EMAIL-011 | 4 | TASK-EMAIL-3.1 | `ResetPassword.jsx` (NUEVO) |
| TASK-EMAIL-4.3 | REQ-EMAIL-005 | 4 | TASK-EMAIL-3.2 | `Settings.jsx` (NUEVO) |
| TASK-EMAIL-5.1 | REQ-EMAIL-007 | 5 | — | `Login.jsx` |
| TASK-EMAIL-5.2 | REQ-EMAIL-014 | 5 | TASK-EMAIL-4.1, TASK-EMAIL-4.2, TASK-EMAIL-4.3 | `App.jsx` |
| TASK-EMAIL-5.3 | REQ-EMAIL-006 | 5 | — | `Sidebar.jsx` |

---

## Notas para la Implementación

### Orden de Implementación Recomendado

Cada fase puede implementarse en orden, y las tareas dentro de cada fase pueden hacerse en el orden listado. Fases 1 y 3 pueden hacerse en paralelo (backend/frontend independiente).

### Discrepancias Spec vs Design

- **Prefijo de ruta para settings**: El spec dice `/api/settings` pero el design (documento de implementación) usa `/api/config`. Seguir el design: prefijo `/api/config` tanto en backend como frontend.
- **POST /api/config/test**: El spec dice `POST /api/settings/test-email`, el design dice `POST /api/config/test`. Seguir el design.

### Funciones Compartidas

- `render_reset_email(reset_url)` — crear como función helper dentro de `routes/auth.py` o en `utils/email.py`. Recomendado: en `utils/email.py` junto a `send_email` para mantener cohesión.

### Variables de Entorno

- `FRONTEND_URL` — usada en `forgot-password` para construir el link de reset. Default: `http://localhost:5173`

### Rate Limiting

- Usar `@limiter.limit("N/period")` del `limiter` ya configurado en `extensions.py`
- Importar desde `from extensions import limiter` (misma práctica que en `auth.py`)
