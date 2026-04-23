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
            <div className="flex items-center gap-2 p-4 mb-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
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
              <input
                type="text"
                name="nombre"
                value={formData.nombre}
                onChange={handleChange}
                placeholder="Nombre"
                required
                className="w-full px-4 py-2.5 rounded-xl input-glass"
              />
              <input
                type="text"
                name="apellido_paterno"
                value={formData.apellido_paterno}
                onChange={handleChange}
                placeholder="Apellido Paterno"
                required
                className="w-full px-4 py-2.5 rounded-xl input-glass"
              />
            </div>

            <input
              type="text"
              name="apellido_materno"
              value={formData.apellido_materno}
              onChange={handleChange}
              placeholder="Apellido Materno"
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            />

            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Correo electrónico"
              required
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            />

            <input
              type="text"
              name="numero_control"
              value={formData.numero_control}
              onChange={handleChange}
              placeholder="Número de Control"
              required
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            />

            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Contraseña"
              required
              minLength={6}
              className="w-full px-4 py-2.5 rounded-xl input-glass"
            />

            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="Confirmar Contraseña"
              required
              className="w-full px-4 py-2.5 rounded-xl input-glass"
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
