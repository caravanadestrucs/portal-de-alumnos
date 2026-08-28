import { useState, useEffect } from 'react';
import { getSedes, createSede, updateSede, deleteSede } from '../../api/sedes';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { Plus, Pencil, Trash2, Building2 } from 'lucide-react';

export default function Sedes() {
  const { isGeneralAdmin } = useAuth();
  const toast = useToast();
  const [sedes, setSedes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nombre: '', codigo: '', direccion: '', activa: true });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchSedes = async () => {
    setLoading(true);
    try {
      const data = await getSedes();
      setSedes(data.sedes || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSedes();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ nombre: '', codigo: '', direccion: '', activa: true });
    setShowModal(true);
  };

  const openEdit = (sede) => {
    setEditing(sede);
    setForm({ nombre: sede.nombre, codigo: sede.codigo, direccion: sede.direccion || '', activa: sede.activa });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await updateSede(editing.id, form);
        toast.success('Sede actualizada');
      } else {
        await createSede(form);
        toast.success('Sede creada');
      }
      setShowModal(false);
      fetchSedes();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al guardar sede');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteSede(deleteTarget.id);
      toast.success('Sede eliminada');
      setDeleteTarget(null);
      fetchSedes();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al eliminar');
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isGeneralAdmin) {
    return (
      <Card>
        <div className="text-center py-8">
          <Building2 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-600">Solo general_admin puede gestionar sedes.</p>
          <p className="text-sm text-gray-500 mt-2">Tu rol: {sedes.length ? 'sede_admin' : 'admin'} — sede asignada {sedes[0]?.codigo || ''}</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Sedes</h1>
          <p className="text-gray-500 mt-1">Gestiona sedes TEO / HUA</p>
        </div>
        <Button onClick={openCreate}>
          <Plus size={18} />
          Nueva Sede
        </Button>
      </div>

      <Card>
        {loading ? (
          <TableSkeleton rows={4} columns={4} />
        ) : sedes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No hay sedes</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Código</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Nombre</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Direccion</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Activa</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {sedes.map((s) => (
                  <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="font-mono font-bold text-primary-700">{s.codigo}</span>
                    </td>
                    <td className="py-3 px-4 text-gray-800">{s.nombre}</td>
                    <td className="py-3 px-4 text-gray-600">{s.direccion || '-'}</td>
                    <td className="py-3 px-4">{s.activa ? 'Sí' : 'No'}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEdit(s)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="Editar">
                          <Pencil size={16} />
                        </button>
                        <button onClick={() => setDeleteTarget(s)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="Eliminar">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Sede' : 'Crear Sede'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          <Input label="Codigo" value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value.toUpperCase() })} required placeholder="TEO, HUA, ..."/>
          <Input label="Direccion" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} placeholder="Dirección" />
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={form.activa} onChange={(e) => setForm({ ...form, activa: e.target.checked })} id="activa" />
            <label htmlFor="activa" className="text-sm">Activa</label>
          </div>
          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)} className="flex-1">Cancelar</Button>
            <Button type="submit" loading={saving} className="flex-1">{editing ? 'Actualizar' : 'Crear'}</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Eliminar sede"
        message={deleteTarget ? `¿Eliminar sede ${deleteTarget.nombre} (${deleteTarget.codigo})?` : ''}
        confirmText="Eliminar"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
