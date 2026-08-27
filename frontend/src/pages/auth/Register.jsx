import { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/index';
import { getCarreras } from '../../api/carreras';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { getEmailError, getNumeroControlError } from '../../utils/validation';

const FALLBACK_ALUMNO_TOKEN = 'ca2d949f-5cd2-4785-918e-205d6566f4e7';
const FALLBACK_PROFESOR_TOKEN = 'ef4a3a25-0214-4581-97dc-5104bb06c748';

export default function Register({ role = 'alumno' }) {
  const { token: inviteToken } = useParams();
  const navigate = useNavigate();
  const { register } = useAuth();

  // SEO: noindex for hidden invite routes
  useEffect(() => {
    const meta = document.createElement('meta');
    meta.name = 'robots';
    meta.content = 'noindex,nofollow';
    document.head.appendChild(meta);
    return () => {
      if (meta.parentNode) meta.parentNode.removeChild(meta);
    };
  }, []);

  const alumnoToken = import.meta.env.VITE_ALUMNO_INVITE_TOKEN || FALLBACK_ALUMNO_TOKEN;
  const profesorToken = import.meta.env.VITE_PROFESOR_INVITE_TOKEN || FALLBACK_PROFESOR_TOKEN;

  // Validate invite token — if it matches neither, show 404 to avoid revealing role
  const isValidToken = inviteToken === alumnoToken || inviteToken === profesorToken;
  // Also enforce role-specific token match: alumno route expects alumno token, profesor route expects profesor token
  const isRoleTokenValid = role === 'alumno' ? inviteToken === alumnoToken : inviteToken === profesorToken;
  const showNotFound = !isValidToken || !isRoleTokenValid;

  const isProfesor = role === 'profesor';

  const [formData, setFormData] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    numero_control: '',
    password: '',
    confirm_password: '',
    carrera_id: '',
  });
  const [carreras, setCarreras] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isProfesor || showNotFound) return;
    // Fetch carreras for alumno selector
    let cancelled = false;
    getCarreras()
      .then((data) => {
        if (!cancelled) setCarreras(data || []);
      })
      .catch(() => {
        if (!cancelled) setCarreras([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isProfesor, showNotFound]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const emailLiveError = getEmailError(formData.email);
  const numeroControlLiveError = !isProfesor ? getNumeroControlError(formData.numero_control) : undefined;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirm_password) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (formData.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    if (!isProfesor && !formData.carrera_id) {
      setError('Seleccioná una carrera');
      return;
    }

    setLoading(true);

    try {
      if (isProfesor) {
        // Call profesor register endpoint directly
        const payload = {
          nombre: formData.nombre,
          apellido_paterno: formData.apellido_paterno,
          apellido_materno: formData.apellido_materno,
          email: formData.email,
          password: formData.password,
          invite_token: inviteToken,
        };
        await api.post('/auth/register/profesor', payload);
        setSuccess('¡Registro exitoso! Ahora puedes iniciar sesión.');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        const { confirm_password, carrera_id, ...rest } = formData;
        const registerData = {
          ...rest,
          carrera_id: Number(carrera_id),
          invite_token: inviteToken,
        };
        await register(registerData);
        setSuccess('¡Registro exitoso! Ahora puedes iniciar sesión.');
        setTimeout(() => navigate('/login'), 2000);
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.message || 'Error al registrar. Intenta de nuevo.';
      // Map backend 404 (invalid invite) to generic "No encontrado"
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (showNotFound) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50 flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">404</h1>
          <p className="text-gray-500">No encontrado</p>
          <Link to="/login" className="text-sm text-primary-600 hover:underline mt-4 inline-block">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const title = isProfesor ? 'Registro de Profesor' : 'Registro de Alumno';
  const subtitle = isProfesor ? 'Solo profesores autorizados pueden registrarse' : 'Solo alumnos autorizados pueden registrarse';

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50 flex items-center justify-center p-4">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary-200/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-accent-200/30 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <img
            src="/logo.png"
            alt="Universidad Felipe Villanueva"
            className="w-24 h-24 mx-auto mb-4"
          />
          <h1 className="text-2xl font-bold gradient-text">Portal de Calificaciones</h1>
          <p className="text-gray-500 mt-1">Universidad Felipe Villanueva</p>
        </div>

        {/* Register Card */}
        <div className="glass p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-2 text-center">
            {title}
          </h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            {subtitle}
          </p>

          {error && (
            <div
              role="alert"
              aria-live="assertive"
              className="flex items-center gap-2 p-4 mb-4 bg-red-50 border border-red-200 rounded-xl text-red-600"
            >
              <AlertCircle size={18} />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 p-4 mb-4 bg-green-50 border border-green-200 rounded-xl text-green-600">
              <CheckCircle size={18} />
              <span className="text-sm">{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Nombre"
                type="text"
                name="nombre"
                id="register-nombre"
                autoComplete="given-name"
                required
                value={formData.nombre}
                onChange={handleChange}
                placeholder="Nombre"
              />
              <Input
                label="Apellido Paterno"
                type="text"
                name="apellido_paterno"
                id="register-apellido-paterno"
                autoComplete="family-name"
                required
                value={formData.apellido_paterno}
                onChange={handleChange}
                placeholder="Apellido Paterno"
              />
            </div>

            <Input
              label="Apellido Materno"
              type="text"
              name="apellido_materno"
              id="register-apellido-materno"
              autoComplete="family-name"
              value={formData.apellido_materno}
              onChange={handleChange}
              placeholder="Apellido Materno"
            />

            <Input
              label="Correo electrónico"
              type="email"
              name="email"
              id="register-email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="correo@ejemplo.com"
              error={emailLiveError}
              helper={!emailLiveError && formData.email ? 'Formato válido' : undefined}
            />

            {!isProfesor && (
              <>
                <Input
                  label="Número de Control"
                  type="text"
                  name="numero_control"
                  id="register-numero-control"
                  autoComplete="off"
                  required
                  value={formData.numero_control}
                  onChange={handleChange}
                  placeholder="Número de Control"
                  error={numeroControlLiveError}
                  helper={!numeroControlLiveError && formData.numero_control ? 'Formato válido: 8-14 alfanuméricos' : undefined}
                />

                <Select
                  label="Carrera"
                  name="carrera_id"
                  id="register-carrera"
                  required
                  value={formData.carrera_id}
                  onChange={handleChange}
                >
                  <option value="">Seleccioná una carrera</option>
                  {carreras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre} ({c.codigo})
                    </option>
                  ))}
                </Select>
              </>
            )}

            <Input
              label="Contraseña"
              type="password"
              name="password"
              id="register-password"
              autoComplete="new-password"
              required
              minLength={6}
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              helper="Mínimo 6 caracteres"
            />

            <Input
              label="Confirmar Contraseña"
              type="password"
              name="confirm_password"
              id="register-confirm-password"
              autoComplete="new-password"
              required
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="••••••••"
            />

            <Button
              type="submit"
              loading={loading}
              className="w-full"
              size="lg"
            >
              Registrarse
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
            >
              ¿Ya tienes cuenta? Inicia sesión
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
