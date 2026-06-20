# Exploration: Email System & Password Recovery

## Current State

El sistema actual no tiene ninguna funcionalidad de email ni recuperación de contraseña. El login es directo con email+password contra 3 tablas (admins, alumnos, profesores). No hay configuración SMTP, no hay envío de correos, no hay flujo de "olvidé mi contraseña". El `change-password` existente requiere sesión activa.

### Arquitectura actual relevante

| Componente | Descripción |
|---|---|
| **Backend: Flask + SQLAlchemy + JWT** | Blueprint pattern, decoradores por rol, tokens JWT con claims `id` y `type` |
| **Frontend: React + Vite + Tailwind** | axios API module pattern, AuthContext con localStorage, ProtectedRoute por rol |
| **Auth**: `routes/auth.py` | Login busca en 3 tablas secuencialmente (admin → profesor → alumno). `generate_tokens()` crea access+refresh JWT |
| **Models**: Admin, Alumno, Profesor | Todos tienen `email` (unique) y `password_hash` con `set_password()`/`check_password()` |
| **Dependencias**: No Flask-Mail | Solo Python stdlib disponible para email (`smtplib`) |
| **UI Components**: Button, Card, Input, Modal, Toast | Patrón consistente en `components/ui/`, toast con `useToast()` hook |
| **Sidebar**: `Sidebar.jsx` | Arrays de rutas por rol (`adminNavItems`, `alumnoNavItems`, `profesorNavItems`) |

## Affected Areas

### Backend
- `backend/models.py` — Agregar modelo `Config` para settings SMTP
- `backend/routes/auth.py` — Agregar endpoints: forgot-password, reset-password
- `backend/utils/security.py` — Agregar función `generate_reset_token()`
- `backend/utils/email.py` — **NUEVO**: Utilidad de envío de email vía smtplib
- `backend/app.py` — Registrar nuevo blueprint si se crea uno separado para settings
- `backend/config.py` — Opcional: agregar defaults SMTP
- `backend/requirements.txt` — Sin cambios necesarios (smtplib es built-in)

### Frontend
- `frontend/src/api/auth.js` — Agregar funciones `forgotPassword()`, `resetPassword()`
- `frontend/src/api/settings.js` — **NUEVO**: API module para settings del sistema
- `frontend/src/pages/auth/Login.jsx` — Agregar link "¿Olvidaste tu contraseña?"
- `frontend/src/pages/auth/ForgotPassword.jsx` — **NUEVO**: Formulario de solicitud de reset
- `frontend/src/pages/auth/ResetPassword.jsx` — **NUEVO**: Formulario de nueva contraseña
- `frontend/src/pages/admin/Settings.jsx` — **NUEVO**: Página de configuración SMTP
- `frontend/src/App.jsx` — Agregar rutas públicas para forgot/reset y ruta protegida para settings
- `frontend/src/components/layout/Sidebar.jsx` — Agregar item "Configuración" al nav de admin

## Approaches

### 1. Almacenamiento de Config SMTP

**Opción A: Modelo key-value (Config)**

```python
class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
```

- **Pros**: Extensible, no requiere migración al agregar nuevas settings, patrón conocido
- **Cons**: Tipado débil (todo string), requiere parseo manual
- **Effort**: Low

**Opción B: Modelo con columnas fijas**

```python
class SmtpConfig(db.Model):
    __tablename__ = 'smtp_config'
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    use_tls = db.Column(db.Boolean, default=True)
```

- **Pros**: Tipado fuerte, queries simples, auto-documentado
- **Cons**: Rígido, requiere migración para cambios
- **Effort**: Low

**Recomendación**: Usar **modelo key-value** para flexibilidad. Es un patrón probado que permite agregar settings sin migraciones.

### 2. Envío de Email

**Opción A: smtplib directo (stdlib)**

- **Pros**: Zero dependencias, control total, ya disponible
- **Cons**: Más código boilerplate, manejo manual de conexiones
- **Effort**: Medium

**Opción B: Flask-Mail**

- **Pros**: Abstracción limpia, integración con Flask
- **Cons**: Dependencia externa, overkill para lo que necesitamos
- **Effort**: Low (si se agrega)

**Recomendación**: Usar **smtplib** con un wrapper utility. Flask-Mail no justifica la dependencia para 2-3 tipos de correo.

### 3. Búsqueda de usuario por email (cross-table)

**Opción única**: Query secuencial o `union_all()`:

```python
def find_user_by_email(email):
    admin = Admin.query.filter_by(email=email).first()
    if admin: return ('admin', admin)
    profesor = Profesor.query.filter_by(email=email).first()
    if profesor: return ('profesor', profesor)
    alumno = Alumno.query.filter_by(email=email).first()
    if alumno: return ('alumno', alumno)
    return None
```

- **Pros**: Sigue el patrón existente de login, simple y predecible
- **Effort**: Low

### 4. Reset Token

**Opción**: JWT con short expiry (15 min) almacenado en columna del modelo o en tabla separada:

```python
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(500), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, alumno, profesor
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Alternativa**: Usar JWT directamente sin almacenar en DB (el token contiene email + role + expiry). 
- **Pros**: Sin DB hits para validar, stateless
- **Cons**: No se puede invalidar individualmente (solo por expiración)

**Recomendación**: Usar **JWT sin almacenamiento** para simplicidad. El short expiry (15 min) mitiga riesgos. Si se necesita invalidación, se agrega después.

### 5. Frontend: Página de Settings

**Opción**: Página standalone en `/admin/configuracion` con un formulario para SMTP + botón "Probar conexión". Sigue el patrón de las páginas admin existentes (Card, Modal, Button, useToast).

## Recommendation

### Arquitectura General

```
email-recovery/
├── backend/
│   ├── models.py                 # + Config model (key-value)
│   ├── routes/auth.py            # + forgot-password, reset-password
│   ├── routes/settings.py        # NUEVO blueprint: GET/PUT config + test email
│   ├── utils/email.py            # NUEVO: send_email() wrapper
│   ├── utils/security.py         # + generate_reset_token(), verify_reset_token()
│   └── app.py                    # + register settings_bp
├── frontend/
│   ├── src/api/auth.js           # + forgotPassword(), resetPassword()
│   ├── src/api/settings.js       # NUEVO: getSettings(), updateSettings(), testEmail()
│   ├── src/pages/auth/Login.jsx  # + link "¿Olvidaste tu contraseña?"
│   ├── src/pages/auth/ForgotPassword.jsx
│   ├── src/pages/auth/ResetPassword.jsx
│   ├── src/pages/admin/Settings.jsx
│   ├── src/App.jsx               # + rutas: /forgot-password, /reset-password, /admin/configuracion
│   └── src/components/layout/Sidebar.jsx  # + item "Configuración"
```

## Data Flow: Password Reset

```
1. User clicks "¿Olvidaste tu contraseña?" en Login
2. GET /forgot-password → formulario email
3. POST /api/auth/forgot-password { email }
   ├── Backend busca user en Admin, Profesor, Alumno
   ├── Si existe → genera JWT reset token (15 min expiry) con { email, role }
   ├── Lee config SMTP de DB → send_email(to, subject, body)
   └── Siempre responde 200 (no revelar si email existe)
4. User revisa email → click link: /reset-password?token=xxx
5. GET /reset-password → formulario nueva contraseña
6. POST /api/auth/reset-password { token, password }
   ├── Backend verifica JWT token
   ├── Busca user por email+role
   ├── Actualiza password_hash
   └── Responde 200
7. User redirigido a /login con mensaje de éxito
```

## Security Considerations

### Críticas
1. **No revelar existencia de email**: El endpoint `forgot-password` debe responder **siempre 200** independientemente de si el email existe. Previene enumeración de cuentas.
2. **Reset token short expiry**: 15 minutos es suficiente. JWT debe usar `SECRET_KEY` de la app.
3. **One-time use tracking**: Aunque sea JWT stateless, agregar columna `used` en un modelo de tokens (o usar `jti` claim + cache) para prevenir reuso si es necesario. Para V1 el short expiry es suficiente.
4. **Rate limiting**: Aplicar `@limiter.limit("5/hour")` en forgot-password para prevenir abuso.
5. **Password complexity**: Validar min 6 chars (mismo estándar existente).
6. **SMTP Password storage**: Almacenar en DB como texto plano es un riesgo. Opciones:
   - **V1**: Almacenar en texto plano (simple, pero asumir el riesgo en entorno controlado)
   - **V2**: Cifrar con `fernet` usando una clave del entorno (`SMTP_ENCRYPTION_KEY`)
   - Recomendación: V1 con advertencia, V2 con cifrado.
7. **Test email**: El endpoint de test debe enviar SOLO al admin autenticado, no permitir指定ar destinatario arbitrario.
8. **CORS**: No hay cambios necesarios, los endpoints están bajo `/api/*`.

### Ready for Proposal

**Yes**. El análisis está completo. Todos los patrones están identificados y las decisiones técnicas son claras.

Resumen de decisiones:

| Decisión | Opción | Razón |
|---|---|---|
| Storage config | Key-value model | Extensible sin migraciones |
| Email sending | smtplib (stdlib) | Zero dependencias |
| Reset token | JWT stateless | Simple, short expiry mitiga riesgo |
| User lookup | Query secuencial | Mismo patrón que login |
| SMTP pass storage | Plain text V1 | Se puede mejorar después |
| Rate limit forgot | 5/hour | Prevenir abuso |
