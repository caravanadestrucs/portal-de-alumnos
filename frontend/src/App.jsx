import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import React, { Suspense, lazy } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToasterProvider } from './components/ui/Toast';

// Layout
import Layout from './components/layout/Layout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminAlumnos from './pages/admin/Alumnos';
import AdminCarreras from './pages/admin/Carreras';
import AdminMaterias from './pages/admin/Materias';
import AdminCalificaciones from './pages/admin/Calificaciones';
import AdminPagos from './pages/admin/Pagos';
import AdminExport from './pages/admin/Export';
import AdminSettings from './pages/admin/Settings';
import AdminProfesores from './pages/admin/Profesores';
import AdminGrupos from './pages/admin/Grupos';
import AdminAsignaciones from './pages/admin/Asignaciones';
import AdminAdmins from './pages/admin/Admins';
import AdminRequisitos from './pages/admin/Requisitos';
// Lazy-loaded heavy pages — split to reduce initial bundle
// TODO S3: virtualización con tanstack-virtual para tablas grandes (Importar preview)
// See frontend/src/hooks/useImport.js and components/import/ImportSteps.jsx placeholders
const AdminImportar = lazy(() => import('./pages/admin/Importar'));
const AdminBoletas = lazy(() => import('./pages/admin/Boletas'));

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

  if (allowedRole && user?.rol !== allowedRole) {
    return <Navigate to={`/${user.rol}`} replace />;
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
    return <Navigate to={`/${user.rol}`} replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToasterProvider>
          <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div></div>}>
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
            {/* Hidden invite-only registration — no public signup. Disallow: /r/ in robots.txt */}
            {/* meta noindex,nofollow is injected by Register component via useEffect for /r/* routes */}
            <Route
              path="/r/a/:token"
              element={
                <PublicRoute>
                  <Register role="alumno" />
                </PublicRoute>
              }
            />
            <Route
              path="/r/p/:token"
              element={
                <PublicRoute>
                  <Register role="profesor" />
                </PublicRoute>
              }
            />
            <Route
              path="/forgot-password"
              element={
                <PublicRoute>
                  <ForgotPassword />
                </PublicRoute>
              }
            />
            <Route
              path="/reset-password"
              element={
                <PublicRoute>
                  <ResetPassword />
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
              <Route path="importar" element={<AdminImportar />} />
              <Route path="boletas" element={<AdminBoletas />} />
              <Route path="admins" element={<AdminAdmins />} />
              {/* <Route path="requisitos" element={<AdminRequisitos />} /> */}
              <Route path="exportar" element={<AdminExport />} />
              <Route path="configuracion" element={<AdminSettings />} />
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
          </Suspense>
        </ToasterProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
