import { useState, useEffect } from 'react';
import { getPeriodos, createPeriodo, updatePeriodo, deletePeriodo } from '../../api/periodos';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { Plus, Pencil, Trash2, CalendarDays } from 'lucide-react';

export default function Periodos() {
  const toast = useToast();
  const [periodos, setPeriodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nombre: '', fecha_inicio: '', fecha_fin: '', activa: true });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchPeriodos = async () => {
    setLoading(true);
    try {
      const data = await getPeriodos();
      setPeriodos(data.periodos || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPeriodos();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ nombre: '', fecha_inicio: '', fecha_fin: '', activa: true });
    setShowModal(true);
  };

  const openEdit = (periodo) => {
    setEditing(periodo);
    setForm({
      nombre: periodo.nombre,
      fecha_inicio: periodo.fecha_inicio || '',
      fecha_fin: periodo.fecha_fin || '',
      activa: periodo.activa,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await updatePeriodo(editing.id, form);
        toast.success('Periodo actualizado');
      } else {
        await createPeriodo(form);
        toast.success('Periodo creado');
      }
      setShowModal(false);
      fetchPeriodos();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al guardar periodo');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deletePeriodo(deleteTarget.id);
      toast.success('Periodo desactivado');
      setDeleteTarget(null);
      fetchPeriodos();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al eliminar');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Periodos</h1>
          <p className="text-gray-500 mt-1">Gestiona los períodos académicos (catálogo para asignaciones y boletas)</p>
        </div>
        <Button onClick={openCreate}>
          <Plus size={18} />
          Nuevo Periodo
        </Button>
      </div>

      <Card>
        {loading ? (
          <TableSkeleton rows={4} columns={5} />
        ) : periodos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No hay periodos</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Nombre</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Fecha inicio</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Fecha fin</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Activa</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {periodos.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-800">{p.nombre}</td>
                    <td className="py-3 px-4 text-gray-600">{p.fecha_inicio || '-'}</td>
                    <td className="py-3 px-4 text-gray-600">{p.fecha_fin || '-'}</td>
                    <td className="py-3 px-4">{p.activa ? 'Sí' : 'No'}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEdit(p)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="Editar">
                          <Pencil size={16} />
                        </button>
                        <button onClick={() => setDeleteTarget(p)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="Desactivar">
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

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Periodo' : 'Crear Periodo'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required placeholder="Ej. Enero-Abril 2026" />
          <Input label="Fecha inicio" type="date" value={form.fecha_inicio} onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })} />
          <Input label="Fecha fin" type="date" value={form.fecha_fin} onChange={(e) => setForm({ ...form, fecha_fin: e.target.value })} />
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
        title="Desactivar periodo"
        message={deleteTarget ? `¿Desactivar el periodo ${deleteTarget.nombre}? No se borra, solo deja de estar disponible para nuevas asignaciones.` : ''}
        confirmText="Desactivar"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}