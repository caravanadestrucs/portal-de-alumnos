import { useState, useEffect } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { useToast } from '../../components/ui/Toast';
import { Eye, EyeOff, Save, Send } from 'lucide-react';
import { getSettings, updateSettings, testEmail } from '../../api/settings';

export default function AdminSettings() {
  const toast = useToast();
  const [formData, setFormData] = useState({
    smtp_host: '',
    smtp_port: '587',
    smtp_email: '',
    smtp_password: '',
    smtp_use_tls: true,
    app_name: '',
    app_logo_url: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [hasPassword, setHasPassword] = useState(false);

  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true);
      try {
        const response = await getSettings();
        const config = response.config || {};
        setFormData((prev) => ({
          ...prev,
          smtp_host: config.smtp_host || '',
          smtp_port: config.smtp_port || '587',
          smtp_email: config.smtp_email || '',
          smtp_password: '',
          smtp_use_tls: config.smtp_use_tls !== 'false',
          app_name: config.app_name || '',
          app_logo_url: config.app_logo_url || '',
        }));
        setHasPassword(!!config.smtp_password);
      } catch (error) {
        console.error('Error loading settings:', error);
        toast.error('Error al cargar la configuración');
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();

    // Client-side validation
    if (!formData.smtp_host.trim()) {
      toast.error('El host SMTP es requerido');
      return;
    }
    const port = parseInt(formData.smtp_port, 10);
    if (isNaN(port) || port < 1 || port > 65535) {
      toast.error('El puerto debe ser un número entre 1 y 65535');
      return;
    }
    if (!formData.smtp_email.trim()) {
      toast.error('El email SMTP es requerido');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.smtp_email)) {
      toast.error('Formato de email inválido');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        ...formData,
        smtp_port: String(formData.smtp_port),
        smtp_use_tls: formData.smtp_use_tls ? 'true' : 'false',
      };
      // Only send password if the user typed something new
      if (!payload.smtp_password) {
        delete payload.smtp_password;
      }
      await updateSettings(payload);
      toast.success('Configuración guardada exitosamente');
      setHasPassword(!!formData.smtp_password || hasPassword);
      setFormData((prev) => ({ ...prev, smtp_password: '' }));
    } catch (error) {
      const message = error.response?.data?.error || 'Error al guardar la configuración';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    setTesting(true);
    try {
      await testEmail();
      toast.success('Email de prueba enviado exitosamente');
    } catch (error) {
      const message = error.response?.data?.error || 'Error al enviar email de prueba';
      toast.error(message);
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Configuración</h1>
          <p className="text-gray-500 mt-1">Cargando configuración...</p>
        </div>
        <div className="grid grid-cols-1 gap-6">
          <Card>
            <div className="animate-pulse space-y-4">
              <div className="h-10 bg-gray-200 rounded-xl w-1/3" />
              <div className="h-10 bg-gray-200 rounded-xl" />
              <div className="h-10 bg-gray-200 rounded-xl" />
              <div className="h-10 bg-gray-200 rounded-xl" />
              <div className="h-10 bg-gray-200 rounded-xl" />
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Configuración</h1>
        <p className="text-gray-500 mt-1">
          Administra la configuración del sistema
        </p>
      </div>

      {/* SMTP Configuration */}
      <Card
        title="Configuración SMTP"
        subtitle="Parámetros del servidor de correo saliente"
      >
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Host SMTP"
              name="smtp_host"
              type="text"
              placeholder="smtp.gmail.com"
              value={formData.smtp_host}
              onChange={handleChange}
            />
            <Input
              label="Puerto SMTP"
              name="smtp_port"
              type="number"
              placeholder="587"
              value={formData.smtp_port}
              onChange={handleChange}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Email SMTP"
              name="smtp_email"
              type="email"
              placeholder="noreply@universidadfv.edu.mx"
              value={formData.smtp_email}
              onChange={handleChange}
            />
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Contraseña SMTP
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="smtp_password"
                  value={formData.smtp_password}
                  onChange={handleChange}
                  placeholder={hasPassword ? '••••••••' : 'Ingresa la contraseña'}
                  className="w-full px-4 py-2.5 rounded-xl input-glass pr-10"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="smtp_use_tls"
              name="smtp_use_tls"
              checked={formData.smtp_use_tls}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  smtp_use_tls: e.target.checked,
                }))
              }
              className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="smtp_use_tls" className="text-sm text-gray-700">
              Usar TLS (STARTTLS)
            </label>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" loading={saving} variant="primary">
              <Save size={18} />
              Guardar configuración
            </Button>
            <Button
              type="button"
              onClick={handleTestEmail}
              loading={testing}
              variant="outline"
            >
              <Send size={18} />
              Enviar email de prueba
            </Button>
          </div>
        </form>
      </Card>

      {/* Personalization */}
      <Card title="Personalización" subtitle="Personaliza la apariencia del sistema">
        <div className="space-y-4">
          <Input
            label="Nombre de la aplicación"
            name="app_name"
            type="text"
            placeholder="Portal de Calificaciones"
            value={formData.app_name}
            onChange={handleChange}
          />
          <Input
            label="URL del Logo"
            name="app_logo_url"
            type="text"
            placeholder="https://ejemplo.com/logo.png"
            value={formData.app_logo_url}
            onChange={handleChange}
          />
        </div>
      </Card>
    </div>
  );
}
