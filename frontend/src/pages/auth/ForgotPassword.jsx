import { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/ui/Button';
import { Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { forgotPassword } from '../../api/auth';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const validateEmail = (value) => {
    if (!value.trim()) {
      return 'El email es requerido';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Formato de email inválido';
    }
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validationError = validateEmail(email);
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      await forgotPassword(email);
    } catch (err) {
      console.error('Error en forgot-password:', err);
    } finally {
      setLoading(false);
      setSubmitted(true);
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

        {/* Card */}
        <div className="glass p-8">
          {submitted ? (
            /* Success Message */
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle size={32} className="text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-800 mb-2">Solicitud enviada</h2>
              <p className="text-sm text-gray-600 mb-6">
                Si el email está registrado, recibirás un enlace de recuperación en tu bandeja de entrada.
              </p>
              <Link
                to="/login"
                className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
              >
                Volver al inicio de sesión
              </Link>
            </div>
          ) : (
            /* Form */
            <>
              <h2 className="text-xl font-bold text-gray-800 mb-2 text-center">
                Recuperar Contraseña
              </h2>
              <p className="text-sm text-gray-500 text-center mb-6">
                Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña.
              </p>

              {error && (
                <div className="flex items-center gap-2 p-4 mb-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
                  <AlertCircle size={18} />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Correo electrónico"
                    required
                    className="w-full pl-10 pr-4 py-3 rounded-xl input-glass"
                  />
                </div>

                <Button
                  type="submit"
                  loading={loading}
                  className="w-full"
                  size="lg"
                >
                  Enviar enlace de recuperación
                </Button>
              </form>

              <div className="mt-6 text-center">
                <Link
                  to="/login"
                  className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
                >
                  Volver al inicio de sesión
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
