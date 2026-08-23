import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    numero_control: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

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

    setLoading(true);

    try {
      const { confirm_password, ...registerData } = formData;
      await register(registerData);
      setSuccess('¡Registro exitoso! Ahora puedes iniciar sesión.');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Error al registrar. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

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
            Registro de Alumno
          </h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            Solo alumnos autorizados pueden registrarse
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
            />

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
            />

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
