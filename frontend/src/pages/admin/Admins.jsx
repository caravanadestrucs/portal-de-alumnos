import { useState, useEffect } from 'react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import { Plus, Pencil, Trash2, Key, Search } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AdminAdmins() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [search, setSearch] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    nombre: '',
    password: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordData, setPasswordData] = useState({
    adminId: null,
    adminName: '',
    newPassword: '',
  });
  const { user } = useAuth();

  const API_URL = import.meta.env.VITE_API_URL || '/api';

  const fetchAdmins = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/admins/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Error al cargar');
      const data = await res.json();
      setAdmins(data.admins || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const openCreate = () => {
    setEditingAdmin(null);
    setFormData({ username: '', email: '', nombre: '', password: '' });
    setError('');
    setShowModal(true);
  };

  const openEdit = (admin) => {
    setEditingAdmin(admin);
    setFormData({
      username: admin.username,
      email: admin.email,
      nombre: admin.nombre,
      password: '',
    });
    setError('');
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    try {
      const token = localStorage.getItem('token');
      const method = editingAdmin ? 'PUT' : 'POST';
      const url = editingAdmin
        ? `${API_URL}/admins/${editingAdmin.id}`
        : `${API_URL}/admins/`;

      const payload = { ...formData };
      if (editingAdmin && !payload.password) {
        delete payload.password;
      }

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error');

      setShowModal(false);
      fetchAdmins();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (admin) => {
    if (!confirm(`¿Eliminar a ${admin.nombre}? Esta acción no se puede deshacer.`)) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/admins/${admin.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Error');
      }

      fetchAdmins();
    } catch (err) {
      alert(err.message);
    }
  };

  const openPasswordModal = (admin) => {
    setPasswordData({
      adminId: admin.id,
      adminName: admin.nombre,
      newPassword: '',
    });
    setShowPasswordModal(true);
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (!passwordData.newPassword || passwordData.newPassword.length < 6) {
      alert('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/admins/${passwordData.adminId}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ new_password: passwordData.newPassword }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Error');
      }

      setShowPasswordModal(false);
      alert('Contraseña actualizada exitosamente');
    } catch (err) {
      alert(err.message);
    }
  };

  const filtered = admins.filter(
    (a) =>
      a.nombre.toLowerCase().includes(search.toLowerCase()) ||
      a.username.toLowerCase().includes(search.toLowerCase()) ||
      a.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Administradores</h1>
          <p className="text-gray-500 mt-1">
            Gestiona los administradores del sistema
          </p>
        </div>
        <Button onClick={openCreate} variant="primary">
          <Plus size={18} />
          Nuevo Administrador
        </Button>
      </div>

      {/* Search */}
      <Card>
        <div className="relative">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar por nombre, usuario o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </Card>

      {/* Lista */}
      <Card title={`Administradores (${filtered.length})`}>
        {loading ? (
          <div className="text-center py-8 text-gray-500">Cargando...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No se encontraron administradores
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Usuario</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Nombre</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((admin) => (
                  <tr key={admin.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-800">{admin.username}</span>
                      {admin.id === user?.id && (
                        <span className="ml-2 text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full">
                          Tú
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-700">{admin.nombre}</td>
                    <td className="py-3 px-4 text-gray-600">{admin.email}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openPasswordModal(admin)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Cambiar contraseña"
                        >
                          <Key size={16} />
                        </button>
                        <button
                          onClick={() => openEdit(admin)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Pencil size={16} />
                        </button>
                        {admin.id !== user?.id && (
                          <button
                            onClick={() => handleDelete(admin)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Eliminar"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal Crear/Editar */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingAdmin ? 'Editar Administrador' : 'Nuevo Administrador'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre de usuario *
            </label>
            <input
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Ej: admin2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo *
            </label>
            <input
              type="text"
              required
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Ej: Juan Pérez"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email *
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Ej: admin@universidadfv.edu.mx"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña {editingAdmin ? '(dejar en blanco para mantener)' : '*'}
            </label>
            <input
              type="password"
              required={!editingAdmin}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder={editingAdmin ? 'Nueva contraseña (opcional)' : 'Mínimo 6 caracteres'}
              minLength={6}
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowModal(false)}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" loading={saving} className="flex-1">
              {editingAdmin ? 'Actualizar' : 'Crear'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Cambiar Contraseña */}
      <Modal
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
        title={`Cambiar Contraseña - ${passwordData.adminName}`}
      >
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nueva Contraseña *
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={passwordData.newPassword}
              onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowPasswordModal(false)}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" className="flex-1">
              Actualizar Contraseña
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
