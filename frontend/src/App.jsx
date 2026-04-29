import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToasterProvider } from './components/ui/Toast';

// Layout
import Layout from './components/layout/Layout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminAlumnos from './pages/admin/Alumnos';
import AdminCarreras from './pages/admin/Carreras';
import AdminMaterias from './pages/admin/Materias';
import AdminCalificaciones from './pages/admin/Calificaciones';
import AdminPagos from './pages/admin/Pagos';
import AdminExport from './pages/admin/Export';
import AdminProfesores from './pages/admin/Profesores';
import AdminGrupos from './pages/admin/Grupos';
import AdminAsignaciones from './pages/admin/Asignaciones';
import AdminRequisitos from './pages/admin/Requisitos';

// Alumno Pages
import AlumnoDashboard from './pages/alumno/Dashboard';
import MisCalificaciones from './pages/alumno/MisCalificaciones';
import MisPagos from './pages/alumno/MisPagos';
import Requisitos from './pages/alumno/Requisitos';

// Profesor Pages
import ProfesorDashboard from './pages/profesor/Dashboard';
import ProfesorCalificaciones from './pages/profesor/Calificaciones';

// Protected Route Component
function ProtectedRoute({ children, allowedRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-accent-50">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && user.type !== allowedRole) {
    return <Navigate to={user.type === 'admin' ? '/admin' : user.type === 'profesor' ? '/profesor' : '/alumno'} replace />;
  }

  return children;
}

// Public Route (redirect if logged in)
function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-accent-50">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to={user.type === 'admin' ? '/admin' : user.type === 'profesor' ? '/profesor' : '/alumno'} replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToasterProvider>
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />

            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRole="admin">
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<AdminDashboard />} />
              <Route path="alumnos" element={<AdminAlumnos />} />
              <Route path="carreras" element={<AdminCarreras />} />
              <Route path="materias" element={<AdminMaterias />} />
              <Route path="calificaciones" element={<AdminCalificaciones />} />
              <Route path="pagos" element={<AdminPagos />} />
              <Route path="profesores" element={<AdminProfesores />} />
              <Route path="grupos" element={<AdminGrupos />} />
              <Route path="asignaciones" element={<AdminAsignaciones />} />
              <Route path="requisitos" element={<AdminRequisitos />} />
              <Route path="exportar" element={<AdminExport />} />
            </Route>

            {/* Alumno Routes */}
            <Route
              path="/alumno"
              element={
                <ProtectedRoute allowedRole="alumno">
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<AlumnoDashboard />} />
              <Route path="calificaciones" element={<MisCalificaciones />} />
              <Route path="pagos" element={<MisPagos />} />
              <Route path="requisitos" element={<Requisitos />} />
            </Route>

            {/* Profesor Routes */}
            <Route
              path="/profesor"
              element={
                <ProtectedRoute allowedRole="profesor">
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<ProfesorDashboard />} />
              <Route path="calificaciones" element={<ProfesorCalificaciones />} />
            </Route>

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </ToasterProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
