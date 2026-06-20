# Propuesta: Sistema de Email y Recuperación de Contraseña

## Resumen
Agregar configuración SMTP y flujo completo de recuperación de contraseña para los 3 roles (admin, alumno, profesor).

## Archivos a Modificar/Crear

### Backend
| Archivo | Acción |
|---------|--------|
| `backend/models.py` | + modelo `Config` key-value |
| `backend/utils/email.py` | **NUEVO** — wrapper SMTP |
| `backend/utils/security.py` | + `generate_reset_token()`, `verify_reset_token()` |
| `backend/routes/auth.py` | + `POST /auth/forgot-password`, `POST /auth/reset-password` |
| `backend/routes/settings.py` | **NUEVO** blueprint — CRUD config + test email |
| `backend/app.py` | + registro `settings_bp` |

### Frontend
| Archivo | Acción |
|---------|--------|
| `frontend/src/api/auth.js` | + `forgotPassword()`, `resetPassword()` |
| `frontend/src/api/settings.js` | **NUEVO** — API module |
| `frontend/src/pages/auth/Login.jsx` | + link "¿Olvidaste tu contraseña?" |
| `frontend/src/pages/auth/ForgotPassword.jsx` | **NUEVO** |
| `frontend/src/pages/auth/ResetPassword.jsx` | **NUEVO** |
| `frontend/src/pages/admin/Settings.jsx` | **NUEVO** — config SMTP + personalización |
| `frontend/src/App.jsx` | + rutas |
| `frontend/src/components/layout/Sidebar.jsx` | + item "Configuración" |

## Decisiones Técnicas
- **Config store**: modelo key-value (`Config.key`, `Config.value`) - extensible sin migraciones
- **Email**: `smtplib` (stdlib) — zero dependencias nuevas
- **Reset token**: JWT stateless, 15 min expiry
- **Rate limit**: 5/hora en forgot-password
- **Seguridad**: forgot-password siempre responde 200 (no revelar existencia)

## Flujo de Recuperación
```
/login → "¿Olvidaste tu contraseña?" → /forgot-password
  → POST /api/auth/forgot-password { email }
  → Busca user en 3 tablas secuencialmente
  → Si existe: JWT (email+role, 15min) → send_email()
  → Siempre responde 200
  → Email con link: /reset-password?token=xxx
    → POST /api/auth/reset-password { token, password }
    → Verifica JWT → busca user → actualiza hash
    → Redirige a /login
```

## Riesgos
- SMTP password en texto plano en DB (V1 aceptable)
- Sin pruebas de integración con SMTP real
- Dependencia de conectividad con servidor SMTP
