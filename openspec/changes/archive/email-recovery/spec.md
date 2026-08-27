# Spec: Sistema de Email y Recuperación de Contraseña

**Change:** `email-recovery`
**Status:** Draft
**Created:** 2026-06-19

---

## 1. SMTP Configuration

### REQ-EMAIL-001 — Modelo de Configuración Key-Value

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-001 |
| **Título** | Modelo `Config` para almacenar configuración |
| **Descripción** | Se debe crear un modelo SQLAlchemy `Config` con los campos `key` (String, unique, not null) y `value` (Text, not null) para almacenar configuración clave-valor en la base de datos. Esto permite almacenar settings SMTP y otros sin necesidad de migraciones futuras. |
| **Prioridad** | MUST |

#### Scenario 1.1 — Crear y leer configuración (Happy Path)

**Given** un modelo `Config` con campos `key` (unique, not null) y `value` (Text, not null)
**When** se crea una entrada con `key="smtp_host"` y `value="smtp.gmail.com"`
**Then** la entrada se persiste en la tabla `config`
**And** se puede recuperar por su key

#### Scenario 1.2 — Clave duplicada (Error Case)

**Given** una entrada existente con `key="smtp_host"`
**When** se intenta crear otra entrada con la misma key
**Then** se lanza una excepción de integridad (unique constraint violation)

#### Scenario 1.3 — Clave vacía (Error Case)

**Given** el modelo `Config`
**When** se intenta crear una entrada con `key=""` o `key=None`
**Then** la operación falla con error de validación

---

### REQ-EMAIL-002 — CRUD de Configuración SMTP (Backend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-002 |
| **Título** | Endpoints CRUD para configuración SMTP |
| **Descripción** | Crear un nuevo Blueprint Flask `settings_bp` con endpoints REST para leer, actualizar y validar la configuración SMTP. Las settings se almacenan como pares key-value en el modelo `Config`. Las claves SMTP son: `smtp_host`, `smtp_port`, `smtp_email`, `smtp_password`, `smtp_use_tls`. |
| **Prioridad** | MUST |

#### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/settings` | Obtener todas las configuraciones (solo admin) |
| `PUT` | `/api/settings` | Actualizar configuraciones SMTP (solo admin) |
| `POST` | `/api/settings/test-email` | Enviar un email de prueba (solo admin) |

#### Scenario 2.1 — Obtener settings exitosamente (Happy Path)

**Given** un admin autenticado
**When** hace `GET /api/settings`
**Then** recibe `200 OK` con un objeto JSON con todas las configuraciones almacenadas
**And** si no hay configuraciones, retorna un objeto vacío `{}`

#### Scenario 2.2 — Actualizar settings SMTP exitosamente (Happy Path)

**Given** un admin autenticado
**When** hace `PUT /api/settings` con body:
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_email": "admin@universidadfv.edu.mx",
  "smtp_password": "secret",
  "smtp_use_tls": true
}
```
**Then** recibe `200 OK`
**And** las configuraciones se persisten en la tabla `config`
**And** se pueden recuperar vía `GET /api/settings`

#### Scenario 2.3 — Actualizar sin autenticación (Error Case)

**Given** un request sin token JWT
**When** hace `PUT /api/settings`
**Then** recibe `401 Unauthorized`

#### Scenario 2.4 — Actualizar con rol no-admin (Error Case)

**Given** un alumno o profesor autenticado
**When** hace `PUT /api/settings`
**Then** recibe `403 Forbidden`

#### Scenario 2.5 — Actualizar con campos inválidos (Error Case)

**Given** un admin autenticado
**When** hace `PUT /api/settings` con `smtp_port="no-un-numero"`
**Then** recibe `400 Bad Request` con mensaje de error de validación

#### Scenario 2.6 — Actualizar con puerto fuera de rango (Error Case)

**Given** un admin autenticado
**When** hace `PUT /api/settings` con `smtp_port=0` o `smtp_port=70000`
**Then** recibe `400 Bad Request` indicando que el puerto debe estar entre 1 y 65535

---

### REQ-EMAIL-003 — Validación de Settings SMTP

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-003 |
| **Título** | Validación de campos SMTP antes de guardar |
| **Descripción** | Antes de persistir cualquier cambio en la configuración SMTP, el backend debe validar: (1) `smtp_host` no vacío, (2) `smtp_port` es entero entre 1 y 65535, (3) `smtp_email` tiene formato de email válido, (4) `smtp_password` no vacío, (5) `smtp_use_tls` es booleano. |
| **Prioridad** | MUST |

#### Scenario 3.1 — Todos los campos requeridos presentes (Happy Path)

**Given** un payload con todos los campos SMTP requeridos y válidos
**When** se ejecuta la validación
**Then** la validación pasa sin errores

#### Scenario 3.2 — Host vacío (Error Case)

**Given** un payload con `smtp_host=""`
**When** se ejecuta la validación
**Then** la validación falla con error `smtp_host es requerido`

#### Scenario 3.3 — Email con formato inválido (Error Case)

**Given** un payload con `smtp_email="invalido"`
**When** se ejecuta la validación
**Then** la validación falla con error indicando formato de email inválido

#### Scenario 3.4 — Password vacío (Error Case)

**Given** un payload con `smtp_password=""` o `smtp_password` ausente
**When** se ejecuta la validación
**Then** la validación falla con error `smtp_password es requerido`

---

### REQ-EMAIL-004 — Test Email Button

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-004 |
| **Título** | Endpoint para enviar email de prueba |
| **Descripción** | El admin puede hacer `POST /api/settings/test-email` para enviar un email de prueba a su propia dirección de email usando la configuración SMTP actual. El endpoint retorna éxito o error según el resultado del envío. |
| **Prioridad** | MUST |

#### Scenario 4.1 — Envío de prueba exitoso (Happy Path)

**Given** configuración SMTP válida almacenada
**And** un admin autenticado con email `admin@universidadfv.edu.mx`
**When** hace `POST /api/settings/test-email`
**Then** el sistema intenta conectarse al servidor SMTP y enviar un email
**And** si el envío es exitoso, retorna `200 OK` con `{"message": "Email de prueba enviado exitosamente"}`

#### Scenario 4.2 — Envío de prueba falla por configuración inválida (Error Case)

**Given** configuración SMTP incompleta o inválida
**And** un admin autenticado
**When** hace `POST /api/settings/test-email`
**Then** retorna `400 Bad Request` con mensaje indicando que la configuración SMTP está incompleta

#### Scenario 4.3 — Envío de prueba falla por conexión SMTP (Error Case)

**Given** configuración SMTP almacenada pero el servidor SMTP es inalcanzable
**And** un admin autenticado
**When** hace `POST /api/settings/test-email`
**Then** retorna `502 Bad Gateway` con mensaje de error de conexión SMTP
**And** la configuración actual NO se elimina ni modifica

---

### REQ-EMAIL-005 — Settings UI (Frontend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-005 |
| **Título** | Página de configuración SMTP en el panel de admin |
| **Descripción** | Crear la página `Settings.jsx` dentro del panel de administración (`/admin/configuracion`) con un formulario para configurar los parámetros SMTP. Incluye un botón "Probar conexión" que envía un email de prueba. Los campos del formulario son: Host, Puerto, Email, Password, Usar TLS (checkbox). Todos los campos excepto password se pre-cargan con los valores almacenados. |
| **Prioridad** | MUST |

#### Scenario 5.1 — Cargar página de settings (Happy Path)

**Given** un admin autenticado
**When** navega a `/admin/configuracion`
**Then** se renderiza el formulario con los campos: Host, Puerto, Email, Password, Usar TLS
**And** los campos Host, Puerto, Email se pre-cargan con los valores almacenados en DB
**And** el campo Password aparece vacío por seguridad

#### Scenario 5.2 — Guardar configuración exitosamente (Happy Path)

**Given** un admin autenticado en la página de configuración
**When** completa todos los campos con valores válidos
**And** hace clic en "Guardar"
**Then** se muestra un indicador de carga
**And** al recibir respuesta exitosa, se muestra un toast de éxito "Configuración guardada"

#### Scenario 5.3 — Guardar con error de validación (Error Case)

**Given** un admin autenticado en la página de configuración
**When** ingresa un puerto inválido (ej: "abc")
**And** hace clic en "Guardar"
**Then** se muestra un mensaje de error en el campo específico
**And** no se envía la petición al backend

#### Scenario 5.4 — Enviar email de prueba (Happy Path)

**Given** un admin autenticado en la página de configuración
**And** la configuración SMTP está completa y guardada
**When** hace clic en "Enviar email de prueba"
**Then** se muestra un indicador de carga en el botón
**And** al recibir respuesta exitosa, se muestra un toast de éxito "Email de prueba enviado"

#### Scenario 5.5 — Email de prueba falla (Error Case)

**Given** un admin autenticado en la página de configuración
**When** hace clic en "Enviar email de prueba"
**And** el backend retorna error de conexión
**Then** se muestra un toast de error con el mensaje del servidor

#### Scenario 5.6 — Acceso denegado para no-admin (Error Case)

**Given** un alumno o profesor autenticado
**When** intenta navegar a `/admin/configuracion`
**Then** es redirigido a su dashboard correspondiente

---

### REQ-EMAIL-006 — Sidebar: Ítem de Configuración

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-006 |
| **Título** | Agregar ítem "Configuración" al menú lateral de admin |
| **Descripción** | Agregar una entrada "Configuración" en el `adminNavItems` del `Sidebar.jsx`, en la última posición antes de "Exportar", con el icono `Settings` de lucide-react y ruta `/admin/configuracion`. |
| **Prioridad** | SHOULD |

#### Scenario 6.1 — Ítem visible para admin (Happy Path)

**Given** un admin autenticado
**When** el Sidebar se renderiza
**Then** se muestra un ítem "Configuración" con el icono de Settings
**And** al hacer clic, navega a `/admin/configuracion`

#### Scenario 6.2 — Ítems no visible para alumno/profesor (Happy Path)

**Given** un alumno o profesor autenticado
**When** el Sidebar se renderiza
**Then** NO se muestra el ítem "Configuración"

---

## 2. Password Recovery Flow

### REQ-EMAIL-007 — "Forgot Password?" Link en Login

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-007 |
| **Título** | Link de recuperación en la página de login |
| **Descripción** | Agregar un link "¿Olvidaste tu contraseña?" debajo del botón de inicio de sesión en `Login.jsx`. El link navega a `/forgot-password`. Debe tener estilos consistentes con el link de registro existente. |
| **Prioridad** | MUST |

#### Scenario 7.1 — Link visible en página de login (Happy Path)

**Given** un usuario no autenticado en la página `/login`
**When** se renderiza el formulario de login
**Then** se muestra un link con texto "¿Olvidaste tu contraseña?" debajo del botón de iniciar sesión
**And** el link tiene ruta `/forgot-password`

#### Scenario 7.2 — Navegación al formulario de recuperación (Happy Path)

**Given** un usuario en `/login`
**When** hace clic en "¿Olvidaste tu contraseña?"
**Then** es redirigido a `/forgot-password`

---

### REQ-EMAIL-008 — Forgot Password Page (Frontend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-008 |
| **Título** | Página "Olvidé mi contraseña" |
| **Descripción** | Crear `ForgotPassword.jsx` en `/forgot-password`. Muestra un formulario con un campo de email. Al enviar, llama a `POST /api/auth/forgot-password`. Siempre muestra el mismo mensaje de éxito independientemente de si el email existe o no (seguridad por obscuridad). |
| **Prioridad** | MUST |

#### Scenario 8.1 — Enviar solicitud de recuperación (Happy Path)

**Given** un usuario no autenticado en `/forgot-password`
**When** ingresa un email en el formulario
**And** hace clic en "Enviar link de recuperación"
**Then** se muestra un indicador de carga
**And** al recibir respuesta, se muestra un mensaje: "Si el email está registrado, recibirás un link de recuperación en tu bandeja de entrada"

#### Scenario 8.2 — Email vacío (Error Case)

**Given** un usuario en `/forgot-password`
**When** hace clic en "Enviar link de recuperación" sin ingresar email
**Then** se muestra un mensaje de validación: "El email es requerido"
**And** no se envía la petición al backend

#### Scenario 8.3 — Email con formato inválido (Error Case)

**Given** un usuario en `/forgot-password`
**When** ingresa "email-invalido"
**And** hace clic en "Enviar link de recuperación"
**Then** se muestra un mensaje de validación: "Formato de email inválido"
**And** no se envía la petición al backend

---

### REQ-EMAIL-009 — Forgot Password Endpoint (Backend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-009 |
| **Título** | `POST /api/auth/forgot-password` |
| **Descripción** | Endpoint público que recibe `{ "email": "..." }`. Busca el email secuencialmente en las tablas `Admin`, `Profesor` y `Alumno`. Si encuentra el usuario, genera un JWT con 15 minutos de expiración que contiene `email`, `role` y `iat`, y envía un email con el link de recuperación. **SIEMPRE retorna 200** independientemente de si el email existe o no, para no revelar qué emails están registrados. |
| **Prioridad** | MUST |

#### Scenario 9.1 — Email existe (Happy Path)

**Given** un email registrado como admin, alumno o profesor
**When** se hace `POST /api/auth/forgot-password` con `{ "email": "user@example.com" }`
**Then** se busca el email primero en `Admin`, luego en `Profesor`, luego en `Alumno`
**And** si se encuentra en cualquiera de las tablas:
  - Se genera un JWT con claims: `{ "email": "...", "role": "admin|alumno|profesor", "iat": <timestamp> }`
  - El JWT tiene expiración de 15 minutos
  - Se envía un email a la dirección con el link: `<frontend_url>/reset-password?token=<jwt>`
**And** se retorna `200 OK` con `{ "message": "Si el email está registrado, recibirás un link de recuperación" }`

#### Scenario 9.2 — Email no existe (Security - No Reveal)

**Given** un email NO registrado en ninguna tabla
**When** se hace `POST /api/auth/forgot-password` con `{ "email": "no-existe@example.com" }`
**Then** **NO** se envía ningún email
**And** se retorna `200 OK` con el mismo mensaje: `{ "message": "Si el email está registrado, recibirás un link de recuperación" }`
**And** el tiempo de respuesta debe ser consistente (sin diferencia perceptible vs. cuando el email existe)

#### Scenario 9.3 — Email inválido (Error Case)

**Given** un request con email mal formado
**When** se hace `POST /api/auth/forgot-password` con `{ "email": "invalido" }`
**Then** se retorna `400 Bad Request` con mensaje de error de validación

#### Scenario 9.4 — Email vacío (Error Case)

**Given** un request sin campo email
**When** se hace `POST /api/auth/forgot-password` con `{}`
**Then** se retorna `400 Bad Request`

#### Scenario 9.5 — Configuración SMTP no configurada (Error Case)

**Given** no hay configuración SMTP en la base de datos
**When** se hace `POST /api/auth/forgot-password` con un email válido y existente
**Then** se retorna `200 OK` (no se revela que no se pudo enviar)
**And** se registra un error en el log del servidor indicando que SMTP no está configurado

#### Scenario 9.6 — Búsqueda secuencial en 3 tablas (Happy Path)

**Given** un email que existe como `Admin`
**When** se hace `POST /api/auth/forgot-password` con ese email
**Then** se encuentra en la tabla `Admin` (sin seguir buscando en `Profesor` o `Alumno`)
**And** el JWT generado contiene `role: "admin"`

**Given** un email que existe solo como `Profesor`
**When** se hace `POST /api/auth/forgot-password` con ese email
**Then** se encuentra en la tabla `Profesor` (después de no encontrarlo en `Admin`)
**And** el JWT generado contiene `role: "profesor"`

**Given** un email que existe solo como `Alumno`
**When** se hace `POST /api/auth/forgot-password` con ese email
**Then** se encuentra en la tabla `Alumno` (después de no encontrarlo en `Admin` ni `Profesor`)
**And** el JWT generado contiene `role: "alumno"`

---

### REQ-EMAIL-010 — JWT Reset Token

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-010 |
| **Título** | Generación y verificación de reset token JWT |
| **Descripción** | En `utils/security.py`, crear dos funciones: (1) `generate_reset_token(email, role)` que genera un JWT con expiración de 15 minutos con claims `email`, `role` y `iat`. (2) `verify_reset_token(token)` que verifica la firma y expiración, y retorna los claims si es válido o lanza excepción si es inválido/expirado. Usar la misma `JWT_SECRET_KEY` de la app. |
| **Prioridad** | MUST |

#### Scenario 10.1 — Token generado correctamente (Happy Path)

**Given** un email y un role válidos
**When** se llama a `generate_reset_token("user@example.com", "alumno")`
**Then** retorna un string JWT firmado con la `JWT_SECRET_KEY`
**And** el token contiene los claims: `email`, `role`, `iat`, `exp`
**And** `exp` está exactamente 15 minutos después de `iat`

#### Scenario 10.2 — Token verificado correctamente (Happy Path)

**Given** un token JWT válido generado por `generate_reset_token`
**When** se llama a `verify_reset_token(token)`
**Then** retorna un dict con `{ "email": "...", "role": "..." }`

#### Scenario 10.3 — Token expirado (Error Case)

**Given** un token JWT con más de 15 minutos de antigüedad
**When** se llama a `verify_reset_token(token)`
**Then** lanza una excepción `TokenExpiredError`

#### Scenario 10.4 — Token con firma inválida (Error Case)

**Given** un token JWT modificado o con firma incorrecta
**When** se llama a `verify_reset_token(token)`
**Then** lanza una excepción de firma inválida

#### Scenario 10.5 — Token malformado (Error Case)

**Given** un string que no es un JWT válido
**When** se llama a `verify_reset_token("string-invalido")`
**Then** lanza una excepción de token inválido

---

### REQ-EMAIL-011 — Reset Password Page (Frontend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-011 |
| **Título** | Página de restablecimiento de contraseña |
| **Descripción** | Crear `ResetPassword.jsx` en `/reset-password`. Lee el token del query string `?token=...`. Muestra un formulario con dos campos: "Nueva contraseña" y "Confirmar nueva contraseña". Valida que la contraseña tenga al menos 6 caracteres y que ambos campos coincidan. Al enviar, llama a `POST /api/auth/reset-password`. En caso de éxito, redirige a `/login` con un mensaje. Si el token es inválido o expiró, muestra un mensaje de error y un link para solicitar un nuevo token. |
| **Prioridad** | MUST |

#### Scenario 11.1 — Reset exitoso (Happy Path)

**Given** un usuario en `/reset-password?token=<token_valido>`
**When** ingresa una nueva contraseña de 8 caracteres en ambos campos
**And** hace clic en "Restablecer contraseña"
**Then** se muestra un indicador de carga
**And** al recibir respuesta exitosa, se redirige a `/login`
**And** se muestra un mensaje de éxito: "Contraseña actualizada exitosamente. Ahora puedes iniciar sesión."

#### Scenario 11.2 — Contraseña muy corta (Error Case)

**Given** un usuario en `/reset-password?token=<token_valido>`
**When** ingresa una contraseña de menos de 6 caracteres
**Then** se muestra un mensaje de validación: "La contraseña debe tener al menos 6 caracteres"
**And** no se envía la petición al backend

#### Scenario 11.3 — Contraseñas no coinciden (Error Case)

**Given** un usuario en `/reset-password?token=<token_valido>`
**When** ingresa contraseñas diferentes en "Nueva contraseña" y "Confirmar nueva contraseña"
**Then** se muestra un mensaje de validación: "Las contraseñas no coinciden"
**And** no se envía la petición al backend

#### Scenario 11.4 — Token inválido o expirado (Error Case)

**Given** un usuario en `/reset-password?token=<token_invalido_o_expirado>`
**When** intenta enviar el formulario
**Then** el backend retorna error 400/401
**And** se muestra un mensaje: "El link de recuperación es inválido o ha expirado"
**And** se muestra un link "Solicitar nuevo link" que redirige a `/forgot-password`

#### Scenario 11.5 — Token ausente (Error Case)

**Given** un usuario en `/reset-password` sin query string `token`
**When** se renderiza la página
**Then** se muestra un mensaje: "Token de recuperación no encontrado"
**And** se muestra un link para ir a `/forgot-password`

---

### REQ-EMAIL-012 — Reset Password Endpoint (Backend)

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-012 |
| **Título** | `POST /api/auth/reset-password` |
| **Descripción** | Endpoint público que recibe `{ "token": "<jwt>", "password": "..." }`. Verifica el token JWT, extrae `email` y `role`, busca al usuario en la tabla correspondiente, actualiza el password hash, y retorna éxito. La nueva contraseña debe tener al menos 6 caracteres. |
| **Prioridad** | MUST |

#### Scenario 12.1 — Reset exitoso para admin (Happy Path)

**Given** un token JWT válido con `email="admin@universidadfv.edu.mx"` y `role="admin"`
**When** se hace `POST /api/auth/reset-password` con `{ "token": "<jwt>", "password": "nueva-pass-123" }`
**Then** se verifica el token JWT
**And** se busca al admin por email en tabla `Admin`
**And** se actualiza `password_hash` con el hash de "nueva-pass-123"
**And** se retorna `200 OK` con `{ "message": "Contraseña actualizada exitosamente" }`

#### Scenario 12.2 — Reset exitoso para alumno (Happy Path)

**Given** un token JWT válido con `email="alumno@example.com"` y `role="alumno"`
**When** se hace `POST /api/auth/reset-password` con `{ "token": "<jwt>", "password": "nueva-pass-123" }`
**Then** se busca al alumno por email en tabla `Alumno`
**And** se actualiza su password_hash
**And** se retorna `200 OK`

#### Scenario 12.3 — Reset exitoso para profesor (Happy Path)

**Given** un token JWT válido con `email="profesor@example.com"` y `role="profesor"`
**When** se hace `POST /api/auth/reset-password` con `{ "token": "<jwt>", "password": "nueva-pass-123" }`
**Then** se busca al profesor por email en tabla `Profesor`
**And** se actualiza su password_hash
**And** se retorna `200 OK`

#### Scenario 12.4 — Token inválido (Error Case)

**Given** un request con un token JWT inválido o expirado
**When** se hace `POST /api/auth/reset-password` con `{ "token": "token-invalido", "password": "nueva-pass-123" }`
**Then** se retorna `400 Bad Request` con mensaje "Token inválido o expirado"

#### Scenario 12.5 — Contraseña muy corta (Error Case)

**Given** un token JWT válido
**When** se hace `POST /api/auth/reset-password` con `{ "token": "<jwt>", "password": "12345" }`
**Then** se retorna `400 Bad Request` con mensaje "La contraseña debe tener al menos 6 caracteres"

#### Scenario 12.6 — Usuario no encontrado (Error Case)

**Given** un token JWT válido con `email="no-existe@example.com"` y `role="admin"`
**When** se hace `POST /api/auth/reset-password` con `{ "token": "<jwt>", "password": "nueva-pass-123" }`
**Then** se busca al admin por email y no se encuentra
**And** se retorna `400 Bad Request` con mensaje "Usuario no encontrado"

#### Scenario 12.7 — Token manipulado con role incorrecto (Error Case)

**Given** un token JWT válido con `email="alumno@example.com"` y `role="admin"`
**When** se hace `POST /api/auth/reset-password`
**Then** se busca al admin por ese email y no existe (porque el email es de alumno)
**And** se retorna `400 Bad Request` con mensaje "Usuario no encontrado"

---

### REQ-EMAIL-013 — Rate Limiting en Forgot Password

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-013 |
| **Título** | Rate limit de 5 solicitudes por hora por IP |
| **Descripción** | El endpoint `POST /api/auth/forgot-password` debe tener un rate limit de 5 requests por hora por dirección IP usando Flask-Limiter. |
| **Prioridad** | MUST |

#### Scenario 13.1 — Requests dentro del límite (Happy Path)

**Given** una IP que no ha hecho solicitudes a `forgot-password` en la última hora
**When** se hacen 5 requests a `POST /api/auth/forgot-password` desde esa IP
**Then** los 5 requests retornan `200 OK`

#### Scenario 13.2 — Límite excedido (Error Case)

**Given** una IP que ya ha hecho 5 requests a `forgot-password` en la última hora
**When** se hace un 6to request desde esa IP
**Then** se retorna `429 Too Many Requests` con mensaje indicando que se excedió el límite

---

### REQ-EMAIL-014 — Rutas Públicas en Frontend

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-014 |
| **Título** | Rutas públicas para forgot-password y reset-password |
| **Descripción** | En `App.jsx`, agregar las rutas `/forgot-password` y `/reset-password` como rutas públicas (usando `PublicRoute` o directamente sin protección) para que usuarios no autenticados puedan acceder. |
| **Prioridad** | MUST |

#### Scenario 14.1 — Acceso a rutas sin autenticación (Happy Path)

**Given** un usuario no autenticado
**When** navega a `/forgot-password`
**Then** se renderiza la página `ForgotPassword`

**Given** un usuario no autenticado
**When** navega a `/reset-password?token=xxx`
**Then** se renderiza la página `ResetPassword`

#### Scenario 14.2 — Redirección si está autenticado (Edge Case)

**Given** un usuario autenticado (sesión activa)
**When** navega a `/forgot-password` o `/reset-password`
**Then** es redirigido a su dashboard (`/admin`, `/alumno` o `/profesor`)
**And** no puede acceder a la página de recuperación

---

## 3. Email Sending Utility

### REQ-EMAIL-015 — Email Utility Module

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-015 |
| **Título** | Módulo `utils/email.py` para envío de emails |
| **Descripción** | Crear `backend/utils/email.py` con una función `send_email(recipient, subject, html_body)` que usa `smtplib` de la stdlib (sin Flask-Mail). Lee la configuración SMTP desde el modelo `Config`. Soporta TLS/STARTTLS. Retorna un dict con `success` (bool) y `error` (str opcional). |
| **Prioridad** | MUST |

#### Requisitos técnicos

- Usar `smtplib.SMTP` de la stdlib de Python
- Leer configuración SMTP desde el modelo `Config` por clave
- Soporte para TLS (puerto 587) y conexión sin TLS (puerto 25)
- Timeout de conexión de 10 segundos
- HTML body con `MIMEText('html', 'html')`
- Encoding UTF-8
- From address extraída de `smtp_email`
- Logging de errores sin exponer detalles sensibles

#### Scenario 15.1 — Envío exitoso con TLS (Happy Path)

**Given** configuración SMTP válida con `smtp_host`, `smtp_port=587`, `smtp_use_tls=true`
**When** se llama a `send_email("destino@example.com", "Asunto", "<html>...</html>")`
**Then** se conecta al servidor SMTP en `smtp_host:587`
**And** se inicia STARTTLS
**And** se autentica con `smtp_email` / `smtp_password`
**And** se envía el email
**And** retorna `{ "success": True }`

#### Scenario 15.2 — Envío exitoso sin TLS (Happy Path)

**Given** configuración SMTP válida con `smtp_port=25`, `smtp_use_tls=false`
**When** se llama a `send_email(...)`
**Then** se conecta al servidor SMTP sin TLS
**And** retorna `{ "success": True }`

#### Scenario 15.3 — Configuración SMTP incompleta (Error Case)

**Given** falta alguna configuración SMTP requerida (`smtp_host`, `smtp_port`, `smtp_email`, `smtp_password`)
**When** se llama a `send_email(...)`
**Then** retorna `{ "success": False, "error": "Configuración SMTP incompleta" }`

#### Scenario 15.4 — Error de conexión SMTP (Error Case)

**Given** configuración SMTP con host inalcanzable o credenciales inválidas
**When** se llama a `send_email(...)`
**Then** retorna `{ "success": False, "error": "Error de conexión SMTP: <mensaje genérico>" }`
**And** el error específico se registra en el log del servidor

---

### REQ-EMAIL-016 — HTML Email Template

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-016 |
| **Título** | Template HTML para email de recuperación |
| **Descripción** | Crear una función o template HTML inline para el email de recuperación. Debe incluir: logo de la universidad, mensaje amigable, botón/link destacado para restablecer contraseña, y un mensaje de que el link expira en 15 minutos. Debe ser responsive y verse bien en clientes de email (Gmail, Outlook, etc.). |
| **Prioridad** | MUST |

#### Scenario 16.1 — Renderizado del template (Happy Path)

**Given** un reset token válido
**When** se genera el HTML del email usando `render_reset_email(token_url)`
**Then** el HTML incluye:
  - Un encabezado con "Recuperación de Contraseña"
  - El logo de la universidad (URL absoluta)
  - Un párrafo indicando que se solicitó un cambio de contraseña
  - Un botón/link estilizado con la URL de reset: `<frontend_url>/reset-password?token=<token>`
  - Texto: "Este link expira en 15 minutos"
  - Texto: "Si no solicitaste este cambio, ignora este mensaje"
  - Footer con "Universidad Felipe Villanueva"

#### Scenario 16.2 — URL de reset correcta (Happy Path)

**Given** un token JWT
**When** se genera la URL de reset
**Then** la URL tiene el formato: `http://<frontend_host>/reset-password?token=<jwt_token>`
**And** el frontend_host se obtiene de configuración o variable de entorno `FRONTEND_URL` con fallback a `http://localhost:5173`

---

### REQ-EMAIL-017 — API Functions: forgotPassword y resetPassword

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-017 |
| **Título** | Funciones API en frontend para recuperación |
| **Descripción** | En `frontend/src/api/auth.js`, agregar dos funciones: `forgotPassword(email)` que hace `POST /api/auth/forgot-password` con `{ email }`, y `resetPassword(token, password)` que hace `POST /api/auth/reset-password` con `{ token, password }`. |
| **Prioridad** | MUST |

#### Scenario 17.1 — forgotPassword exitoso (Happy Path)

**Given** la función `forgotPassword` implementada
**When** se llama con `forgotPassword("user@example.com")`
**Then** hace `POST /api/auth/forgot-password` con body `{ "email": "user@example.com" }`
**And** retorna la respuesta del servidor

#### Scenario 17.2 — resetPassword exitoso (Happy Path)

**Given** la función `resetPassword` implementada
**When** se llama con `resetPassword("jwt-token", "nueva-pass-123")`
**Then** hace `POST /api/auth/reset-password` con body `{ "token": "jwt-token", "password": "nueva-pass-123" }`
**And** retorna la respuesta del servidor

---

### REQ-EMAIL-018 — Settings API Module

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-018 |
| **Título** | Módulo API `settings.js` en frontend |
| **Descripción** | Crear `frontend/src/api/settings.js` con funciones `getSettings()`, `updateSettings(data)` y `testEmail()` que llaman a los endpoints correspondientes del backend. |
| **Prioridad** | MUST |

#### Scenario 18.1 — getSettings (Happy Path)

**Given** el módulo `settings.js` implementado
**When** se llama a `getSettings()`
**Then** hace `GET /api/settings`
**And** retorna el objeto con todas las configuraciones

#### Scenario 18.2 — updateSettings (Happy Path)

**Given** el módulo `settings.js` implementado
**When** se llama a `updateSettings({ smtp_host: "smtp.gmail.com", ... })`
**Then** hace `PUT /api/settings` con el payload
**And** retorna la respuesta del servidor

#### Scenario 18.3 — testEmail (Happy Path)

**Given** el módulo `settings.js` implementado
**When** se llama a `testEmail()`
**Then** hace `POST /api/settings/test-email`
**And** retorna la respuesta del servidor

---

### REQ-EMAIL-019 — Registro del Blueprint settings_bp

| Campo | Valor |
|-------|-------|
| **ID** | REQ-EMAIL-019 |
| **Título** | Registrar `settings_bp` en la app Flask |
| **Descripción** | En `backend/app.py`, importar y registrar el nuevo Blueprint `settings_bp` con url_prefix `/api/settings`. |
| **Prioridad** | MUST |

#### Scenario 19.1 — Blueprint registrado (Happy Path)

**Given** la aplicación Flask
**When** se importa `settings_bp` desde `routes.settings`
**And** se registra con `app.register_blueprint(settings_bp, url_prefix='/api/settings')`
**Then** los endpoints de settings están disponibles en `/api/settings`

---

## Matriz de Trazabilidad

| REQ ID | Descripción | Prioridad | Backend | Frontend | Depende de |
|--------|-------------|-----------|---------|----------|------------|
| REQ-EMAIL-001 | Modelo Config key-value | MUST | `models.py` | — | — |
| REQ-EMAIL-002 | CRUD settings SMTP | MUST | `routes/settings.py` | — | REQ-EMAIL-001 |
| REQ-EMAIL-003 | Validación campos SMTP | MUST | `routes/settings.py` | — | REQ-EMAIL-002 |
| REQ-EMAIL-004 | Test email endpoint | MUST | `routes/settings.py` | — | REQ-EMAIL-002, REQ-EMAIL-015 |
| REQ-EMAIL-005 | Settings UI | MUST | — | `Settings.jsx` | REQ-EMAIL-002, REQ-EMAIL-018 |
| REQ-EMAIL-006 | Sidebar item | SHOULD | — | `Sidebar.jsx` | REQ-EMAIL-005 |
| REQ-EMAIL-007 | Forgot password link | MUST | — | `Login.jsx` | — |
| REQ-EMAIL-008 | Forgot password page | MUST | — | `ForgotPassword.jsx` | REQ-EMAIL-017 |
| REQ-EMAIL-009 | Forgot password endpoint | MUST | `routes/auth.py` | — | REQ-EMAIL-010, REQ-EMAIL-015, REQ-EMAIL-013 |
| REQ-EMAIL-010 | JWT reset token utils | MUST | `utils/security.py` | — | — |
| REQ-EMAIL-011 | Reset password page | MUST | — | `ResetPassword.jsx` | REQ-EMAIL-017 |
| REQ-EMAIL-012 | Reset password endpoint | MUST | `routes/auth.py` | — | REQ-EMAIL-010 |
| REQ-EMAIL-013 | Rate limiting | MUST | `routes/auth.py` | — | REQ-EMAIL-009 |
| REQ-EMAIL-014 | Public routes | MUST | — | `App.jsx` | REQ-EMAIL-008, REQ-EMAIL-011 |
| REQ-EMAIL-015 | Email utility module | MUST | `utils/email.py` | — | REQ-EMAIL-001 |
| REQ-EMAIL-016 | HTML email template | MUST | `utils/email.py` | — | REQ-EMAIL-015 |
| REQ-EMAIL-017 | Auth API functions | MUST | — | `api/auth.js` | — |
| REQ-EMAIL-018 | Settings API module | MUST | — | `api/settings.js` | — |
| REQ-EMAIL-019 | Register settings blueprint | MUST | `app.py` | — | REQ-EMAIL-002 |

---

## Consideraciones de Seguridad

1. **No revelar existencia de emails**: El endpoint `forgot-password` SIEMPRE retorna 200, independientemente de si el email existe o no. El tiempo de respuesta debe ser consistente para evitar timing attacks.
2. **JWT de corta duración**: Los reset tokens expiran en 15 minutos.
3. **Rate limiting**: 5 requests por hora por IP en forgot-password para prevenir abusos.
4. **Contraseña en texto plano en DB**: Aceptado para V1. En futuras versiones se debería cifrar el valor de `smtp_password`.
5. **Validación de token**: El reset token incluye `email` y `role` para asegurar que el usuario solo puede resetear su propia contraseña en la tabla correcta.
6. **Sin dependencias nuevas**: Se usa `smtplib` de la stdlib. No se agrega Flask-Mail ni otras dependencias.
