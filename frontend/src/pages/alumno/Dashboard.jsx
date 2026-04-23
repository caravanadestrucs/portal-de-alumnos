import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import { getMisDatos } from '../../api/alumnos';
import { getPagosByAlumno } from '../../api/pagos';
import { FileText, CreditCard, GraduationCap, User, TrendingUp } from 'lucide-react';

export default function AlumnoDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    promedio: null,
    practicasCompletadas: 0,
    totalPracticas: 2,
    pagosPendientes: 0,
  });

  useEffect(() => {
    const loadStats = async () => {
      try {
        // Load pagos for the current alumno
        const pagos = await getPagosByAlumno(user?.id).catch(() => []);
        
        if (Array.isArray(pagos)) {
          const pending = pagos.filter(p => !p.pagada).length;
          setStats(prev => ({ ...prev, pagosPendientes: pending }));
        }
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    };

    if (user?.id) {
      loadStats();
    }
  }, [user]);

  const menuItems = [
    {
      title: 'Mis Calificaciones',
      description: 'Consulta tu historial académico completo',
      icon: FileText,
      path: '/alumno/calificaciones',
      color: 'from-primary-500 to-primary-600',
    },
    {
      title: 'Mis Pagos',
      description: 'Revisa tu estado de cuenta y pagos pendientes',
      icon: CreditCard,
      path: '/alumno/pagos',
      color: 'from-accent-500 to-accent-600',
      badge: stats.pagosPendientes > 0 ? `${stats.pagosPendientes} pendiente(s)` : null,
    },
    {
      title: 'Requisitos de Titulación',
      description: 'Prácticas profesionales y requisitos',
      icon: GraduationCap,
      path: '/alumno/requisitos',
      color: 'from-purple-500 to-purple-600',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="glass p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg">
            {user?.nombre?.charAt(0) || 'A'}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              ¡Bienvenido, {user?.nombre || 'Alumno'}!
            </h1>
            <p className="text-gray-500 mt-1">
              Universidad Felipe Villanueva
            </p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="info">
                {user?.numero_control || 'Sin número de control'}
              </Badge>
              {user?.carrera?.nombre && (
                <Badge variant="default">{user.carrera.nombre}</Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="text-center">
          <TrendingUp size={28} className="mx-auto text-primary-500 mb-2" />
          <p className="text-sm text-gray-500">Promedio General</p>
          <p className="text-2xl font-bold text-gray-800">
            {stats.promedio ? stats.promedio.toFixed(1) : '-'}
          </p>
        </Card>
        <Card className="text-center">
          <GraduationCap size={28} className="mx-auto text-purple-500 mb-2" />
          <p className="text-sm text-gray-500">Prácticas</p>
          <p className="text-2xl font-bold text-gray-800">
            {stats.practicasCompletadas}/{stats.totalPracticas}
          </p>
        </Card>
        <Card className="text-center">
          <CreditCard size={28} className="mx-auto text-orange-500 mb-2" />
          <p className="text-sm text-gray-500">Pagos Pendientes</p>
          <p className="text-2xl font-bold text-gray-800">
            {stats.pagosPendientes}
          </p>
        </Card>
      </div>

      {/* Menu Cards */}
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Mi Panel</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <Card
                key={item.path}
                hover
                className="cursor-pointer relative overflow-hidden"
                onClick={() => navigate(item.path)}
              >
                <div
                  className={`absolute top-0 right-0 w-24 h-24 rounded-full bg-gradient-to-br ${item.color} opacity-10 transform translate-x-8 -translate-y-8`}
                />
                <div className="relative">
                  <div
                    className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${item.color} flex items-center justify-center shadow-lg mb-4`}
                  >
                    <Icon size={28} className="text-white" />
                  </div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-800">{item.title}</h3>
                    {item.badge && (
                      <Badge variant="warning">{item.badge}</Badge>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{item.description}</p>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <User size={20} className="text-primary-600" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              ¿Necesitas ayuda?
            </h4>
            <p className="text-sm text-gray-500">
              Si tienes alguna duda sobre tus calificaciones, pagos o requisitos,
              contacta al departamento académico. Estamos para ayudarte.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
