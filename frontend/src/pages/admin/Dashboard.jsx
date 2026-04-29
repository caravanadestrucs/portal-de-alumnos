import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import { getAlumnos } from '../../api/alumnos';
import { getCarreras } from '../../api/carreras';
import { getMaterias } from '../../api/materias';
import { getAlumnosConPagosPendientes } from '../../api/pagos';
import {
  Users,
  GraduationCap,
  BookOpen,
  FileText,
  CreditCard,
  TrendingUp,
  Clock,
} from 'lucide-react';

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    alumnos: 0,
    carreras: 0,
    materias: 0,
    pagosPendientes: 0,
    alumnosConDeuda: 0,
    totalAdeudo: 0,
  });

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [alumnos, carreras, materias, pagosData] = await Promise.all([
          getAlumnos().catch(() => []),
          getCarreras().catch(() => []),
          getMaterias().catch(() => []),
          getAlumnosConPagosPendientes().catch(() => ({ alumnos: [], total_adeudo: 0 })),
        ]);

        setStats({
          alumnos: Array.isArray(alumnos) ? alumnos.length : 0,
          carreras: Array.isArray(carreras) ? carreras.length : 0,
          materias: Array.isArray(materias) ? materias.length : 0,
          pagosPendientes: Array.isArray(pagosData.alumnos) ? pagosData.alumnos.length : 0,
          alumnosConDeuda: Array.isArray(pagosData.alumnos) ? pagosData.alumnos.length : 0,
          totalAdeudo: pagosData.total_adeudo || 0,
        });
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    };

    loadStats();
  }, []);

  const statCards = [
    {
      title: 'Alumnos',
      value: stats.alumnos,
      icon: Users,
      color: 'from-primary-500 to-primary-600',
      path: '/admin/alumnos',
    },
    {
      title: 'Carreras',
      value: stats.carreras,
      icon: GraduationCap,
      color: 'from-accent-500 to-accent-600',
      path: '/admin/carreras',
    },
    {
      title: 'Materias',
      value: stats.materias,
      icon: BookOpen,
      color: 'from-purple-500 to-purple-600',
      path: '/admin/materias',
    },
    {
      title: 'Alumnos Deuda',
      value: stats.alumnosConDeuda,
      subtitle: `$${stats.totalAdeudo.toLocaleString('es-MX', { minimumFractionDigits: 2 })} total`,
      icon: CreditCard,
      color: 'from-orange-500 to-orange-600',
      path: '/admin/pagos',
    },
  ];

  const quickActions = [
    {
      title: 'Calificaciones',
      description: 'Gestionar calificaciones de alumnos',
      icon: FileText,
      path: '/admin/calificaciones',
    },
    {
      title: 'Exportar Datos',
      description: 'Descargar SQL o Excel',
      icon: TrendingUp,
      path: '/admin/exportar',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">
            ¡Bienvenido, {user?.nombre || 'Admin'}!
          </h1>
          <p className="text-gray-500 mt-1">
            Panel de administración - Universidad Felipe Villanueva
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock size={16} />
          <span>{new Date().toLocaleDateString('es-MX', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card
              key={stat.title}
              hover
              className="cursor-pointer"
              onClick={() => navigate(stat.path)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-800 mt-1">
                    {stat.value}
                  </p>
                  {stat.subtitle && (
                    <p className="text-xs text-orange-600 font-medium mt-1">
                      {stat.subtitle}
                    </p>
                  )}
                </div>
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-lg`}>
                  <Icon size={24} className="text-white" />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Card
                key={action.title}
                hover
                className="cursor-pointer"
                onClick={() => navigate(action.path)}
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-md">
                    <Icon size={24} className="text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">{action.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{action.description}</p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Recent Activity Placeholder */}
      <Card title="Actividad Reciente" subtitle="Últimas acciones en el sistema">
        <div className="text-center py-8 text-gray-500">
          <p>No hay actividad reciente</p>
          <p className="text-sm mt-1">Las acciones aparecerán aquí</p>
        </div>
      </Card>
    </div>
  );
}
