import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Button from '../../components/ui/Button';
import { Lock, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { resetPassword } from '../../api/auth';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [tokenError, setTokenError] = useState('');

  const validate = () => {
    if (password.length < 6) {
      return 'La contraseña debe tener al menos 6 caracteres';
    }
    if (password !== confirmPassword) {
      return 'Las contraseñas no coinciden';
    }
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      await resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      const message = err.response?.data?.error || 'El link de recuperación es inválido o ha expirado';
      setTokenError(message);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    /* No token in URL */
    if (!token) {
      return (
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle size={32} className="text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Token no encontrado</h2>
          <p className="text-sm text-gray-600 mb-6">
            Token de recuperación no encontrado. Solicita un nuevo link de recuperación.
          </p>
          <Link
            to="/forgot-password"
            className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
          >
            Solicitar nuevo link
          </Link>
        </div>
      );
    }

    /* Token inválido — error del backend */
    if (tokenError) {
      return (
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle size={32} className="text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Link inválido o expirado</h2>
          <p className="text-sm text-gray-600 mb-6">{tokenError}</p>
          <Link
            to="/forgot-password"
            className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
          >
            Solicitar nuevo link
          </Link>
        </div>
      );
    }

    /* Success */
    if (success) {
      return (
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Contraseña actualizada</h2>
          <p className="text-sm text-gray-600 mb-6">
            Contraseña actualizada exitosamente. Ahora puedes iniciar sesión.
          </p>
          <Link
            to="/login"
            className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
          >
            Ir a Iniciar Sesión
          </Link>
        </div>
      );
    }

    /* Formulario */
    return (
      <>
        <h2 className="text-xl font-bold text-gray-800 mb-2 text-center">
          Restablecer Contraseña
        </h2>
        <p className="text-sm text-gray-500 text-center mb-6">
          Ingresa tu nueva contraseña.
        </p>

        {error && (
          <div className="flex items-center gap-2 p-4 mb-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Nueva contraseña"
              required
              minLength={6}
              className="w-full pl-10 pr-10 py-3 rounded-xl input-glass"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <div className="relative">
            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirmar nueva contraseña"
              required
              minLength={6}
              className="w-full pl-10 pr-4 py-3 rounded-xl input-glass"
            />
          </div>

          <Button
            type="submit"
            loading={loading}
            className="w-full"
            size="lg"
          >
            Restablecer contraseña
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link
            to="/forgot-password"
            className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
          >
            Solicitar nuevo link
          </Link>
        </div>
      </>
    );
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
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
