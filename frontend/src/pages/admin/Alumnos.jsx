import { useState, useEffect, useCallback } from 'react';
import { getAlumnos, createAlumno, updateAlumno, deleteAlumno, sendBulkCredentials } from '../../api/alumnos';
import { getCarreras } from '../../api/carreras';
import { useFetch } from '../../hooks/useFetch';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Badge from '../../components/ui/Badge';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import ProgressModal from '../../components/ui/ProgressModal';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { Plus, Search, Edit, Trash2, UserPlus, ChevronLeft, ChevronRight, Mail } from 'lucide-react';

const ITEMS_PER_PAGE = 10;

export default function AdminAlumnos() {
  const { data: carreras } = useFetch(getCarreras);

  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAlumno, setEditingAlumno] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    numero_control: '',
    password: '',
    carrera_id: '',
  });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  // bulk selection
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showBulkConfirm, setShowBulkConfirm] = useState(false);
  const [bulkSending, setBulkSending] = useState(false);
  const [bulkResults, setBulkResults] = useState(null); // [{id,email,status,error}]
  const [showProgress, setShowProgress] = useState(false);
  const toast = useToast();

  // ── Debounce del search ──────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchTerm(searchTerm), 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // ── Resetear a página 1 cuando cambia la búsqueda ────────
  useEffect(() => {
    setPage(1);
  }, [debouncedSearchTerm]);

  // ── Fetch de alumnos con paginación y búsqueda ───────────
  const fetchAlumnos = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getAlumnos({
        page,
        per_page: ITEMS_PER_PAGE,
        search: debouncedSearchTerm || undefined,
      });
      setAlumnos(result.alumnos || []);
      setTotalItems(result.total || 0);
      setTotalPages(result.pages || 0);
      return result;
    } catch (err) {
      console.error('Error al cargar alumnos:', err);
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearchTerm]);

  useEffect(() => {
    fetchAlumnos();
  }, [fetchAlumnos]);

  // ── Bulk helpers ───────────────────────────────────────
  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const toggleSelectAll = () => {
    if (selectedIds.size === alumnos.length && alumnos.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(alumnos.map((a) => a.id)));
    }
  };
  const allSelected = alumnos.length > 0 && selectedIds.size === alumnos.length;

  const handleConfirmBulk = async () => {
    const ids = Array.from(selectedIds);
    setBulkSending(true);
    try {
      const data = await sendBulkCredentials(ids, true);
      const results = data.results || [];
      setBulkResults(results);
      setShowBulkConfirm(false);
      setShowProgress(true);
      const sent = results.filter((r) => r.status === 'sent').length;
      const failed = results.filter((r) => r.status === 'failed').length;
      if (failed === 0) toast.success(`Credenciales enviadas a ${sent} alumnos`);
      else if (sent === 0) toast.error(`Falló envío a ${failed} alumnos`);
      else toast.success(`Enviados ${sent}, fallidos ${failed}`);
    } catch (err) {
      const msg = err.response?.data?.error || 'Error al enviar credenciales';
      toast.error(msg);
    } finally {
      setBulkSending(false);
    }
  };

  const handleRetryFailed = async (failedIds) => {
    setBulkSending(true);
    try {
      const data = await sendBulkCredentials(failedIds, true);
      const newResults = data.results || [];
      // merge: replace failed entries with new status
      setBulkResults((prev) => {
        if (!prev) return newResults;
        const map = new Map(newResults.map((r) => [r.id, r]));
        return prev.map((r) => (map.has(r.id) ? map.get(r.id) : r));
      });
      const sentRetry = newResults.filter((r) => r.status === 'sent').length;
      toast.success(`Reintento: ${sentRetry} enviados`);
    } catch (err) {
      toast.error('Error al reintentar');
    } finally {
      setBulkSending(false);
    }
  };

  // ── Columnas de la tabla ─────────────────────────────────
  const columns = [
    {
      key: 'select',
      header: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleSelectAll}
          aria-label="Seleccionar todos"
        />
      ),
      width: '40px',
      render: (row) => (
        <input
          type="checkbox"
          checked={selectedIds.has(row.id)}
          onChange={() => toggleSelect(row.id)}
          aria-label={`Seleccionar ${row.email}`}
        />
      ),
    },
    {
      key: 'numero_control',
      header: 'No. Control',
      width: '120px',
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (row) =>
        `${row.nombre} ${row.apellido_paterno} ${row.apellido_materno || ''}`.trim(),
    },
    {
      key: 'email',
      header: 'Email',
    },
    {
      key: 'carrera',
      header: 'Carrera',
      render: (row) => row.carrera?.nombre || '-',
    },
    {
      key: 'activo',
      header: 'Estado',
      render: (row) => (
        <Badge variant={row.activo ? 'success' : 'danger'}>
          {row.activo ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Acciones',
      width: '150px',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openEditModal(row);
            }}
            className="p-2 hover:bg-primary-50 rounded-lg transition-colors"
          >
            <Edit size={16} className="text-primary-600" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDeleteTarget(row);
            }}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
            aria-label={`Eliminar alumno ${row.nombre}`}
          >
            <Trash2 size={16} className="text-red-500" />
          </button>
        </div>
      ),
    },
  ];

  // ── Helpers del modal ────────────────────────────────────
  const openNewModal = () => {
    setEditingAlumno(null);
    setFormData({
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      email: '',
      numero_control: '',
      password: '',
      carrera_id: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (alumno) => {
    setEditingAlumno(alumno);
    setFormData({
      nombre: alumno.nombre,
      apellido_paterno: alumno.apellido_paterno,
      apellido_materno: alumno.apellido_materno || '',
      email: alumno.email,
      numero_control: alumno.numero_control,
      password: '',
      carrera_id: alumno.carrera_id || '',
    });
    setIsModalOpen(true);
  };

  // ── CRUD handlers ────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (editingAlumno) {
        const { password, ...updateData } = formData;
        await updateAlumno(editingAlumno.id, updateData);
        await fetchAlumnos(); // recargar página actual
      } else {
        await createAlumno(formData);
        setPage(1); // ir a primera página para ver el nuevo
      }
      setIsModalOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteAlumno(deleteTarget.id);
      toast.success('Alumno eliminado');
      const result = await fetchAlumnos();
      if (result && result.alumnos && result.alumnos.length === 0 && page > 1) {
        setPage((p) => p - 1);
      }
      setDeleteTarget(null);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Error al eliminar');
    } finally {
      setIsDeleting(false);
    }
  };

  // ── Paginación ───────────────────────────────────────────
  const firstItem = (page - 1) * ITEMS_PER_PAGE + 1;
  const lastItem = Math.min(page * ITEMS_PER_PAGE, totalItems);

  const getPageNumbers = () => {
    if (totalPages <= 1) return [];

    const pages = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push('...');
      for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
        pages.push(i);
      }
      if (page < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  const pageNumbers = getPageNumbers();

  // ── Render ───────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Alumnos</h1>
          <p className="text-gray-500 mt-1">
            Gestionar alumnos registrados
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            disabled={selectedIds.size === 0}
            title={selectedIds.size === 0 ? 'Select at least one student' : `${selectedIds.size} seleccionados`}
            onClick={() => setShowBulkConfirm(true)}
          >
            <Mail size={16} />
            Enviar credenciales ({selectedIds.size})
          </Button>
          <Button onClick={openNewModal}>
            <UserPlus size={18} />
            Nuevo Alumno
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nombre, número de control o email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-12 pr-4 py-3 rounded-xl input-glass"
        />
      </div>

      {/* Table */}
      {loading ? (
        <TableSkeleton rows={8} columns={5} />
      ) : alumnos.length === 0 ? (
        <Card className="text-center py-12">
          <UserPlus size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 mb-4">No hay alumnos registrados</p>
          <Button onClick={openNewModal}>
            <Plus size={18} />
            Crear primer alumno
          </Button>
        </Card>
      ) : (
        <Table
          columns={columns}
          data={alumnos}
          emptyMessage="No hay alumnos registrados"
        />
      )}

      {/* Pagination */}
      {totalPages > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <p className="text-sm text-gray-500">
            Mostrando {firstItem}&ndash;{lastItem} de {totalItems} alumnos
          </p>

          {pageNumbers.length > 0 && (
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft size={16} />
                Anterior
              </Button>

              {pageNumbers.map((pageNum, idx) =>
                pageNum === '...' ? (
                  <span key={`ellipsis-${idx}`} className="px-2 text-gray-400 select-none">
                    ...
                  </span>
                ) : (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                      pageNum === page
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              )}

              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
                <ChevronRight size={16} />
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingAlumno ? 'Editar Alumno' : 'Nuevo Alumno'}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} loading={saving}>
              {editingAlumno ? 'Guardar Cambios' : 'Crear Alumno'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre"
              name="nombre"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              required
            />
            <Input
              label="Apellido Paterno"
              name="apellido_paterno"
              value={formData.apellido_paterno}
              onChange={(e) => setFormData({ ...formData, apellido_paterno: e.target.value })}
              required
            />
          </div>

          <Input
            label="Apellido Materno"
            name="apellido_materno"
            value={formData.apellido_materno}
            onChange={(e) => setFormData({ ...formData, apellido_materno: e.target.value })}
          />

          <Input
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />

          <Input
            label="Número de Control"
            name="numero_control"
            value={formData.numero_control}
            onChange={(e) => setFormData({ ...formData, numero_control: e.target.value })}
            required
          />

          <Select
            label="Carrera"
            value={formData.carrera_id}
            onChange={(e) => setFormData({ ...formData, carrera_id: e.target.value })}
            required
          >
            <option value="">Seleccionar carrera</option>
            {Array.isArray(carreras) &&
              carreras.map((carrera) => (
                <option key={carrera.id} value={carrera.id}>
                  {carrera.nombre}
                </option>
              ))}
          </Select>

          {!editingAlumno ? (
            <Input
              label="Contraseña"
              name="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              helper="Mínimo 6 caracteres"
            />
          ) : (
            <div className="space-y-2">
              <Input
                label="Nueva Contraseña (dejar vacío para mantener la actual)"
                name="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                helper="Mínimo 6 caracteres"
              />
              <button
                type="button"
                onClick={() => {
                  const newPassword = Math.random().toString(36).slice(-6);
                  setFormData({ ...formData, password: newPassword });
                }}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                🔄 Generar contraseña aleatoria
              </button>
            </div>
          )}
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Eliminar alumno"
        message={
          deleteTarget
            ? `¿Eliminar a ${deleteTarget.nombre} ${deleteTarget.apellido_paterno || ''} (${deleteTarget.numero_control})?`
            : '¿Eliminar este alumno?'
        }
        impactSummary="Se eliminarán sus calificaciones, pagos y prácticas. Esta acción no se puede deshacer."
        confirmText="Eliminar"
        variant="danger"
        isLoading={isDeleting}
      />

      {/* Bulk confirm */}
      <ConfirmDialog
        isOpen={showBulkConfirm}
        onClose={() => setShowBulkConfirm(false)}
        onConfirm={handleConfirmBulk}
        title="Enviar credenciales"
        message={
          selectedIds.size > 0
            ? `Se enviarán credenciales temporales (expiran en 24h) a ${selectedIds.size} alumnos: ${alumnos.filter((a) => selectedIds.has(a.id)).map((a) => a.email).join(', ')}`
            : 'Seleccioná al menos un alumno'
        }
        confirmText={bulkSending ? 'Enviando...' : `Enviar a ${selectedIds.size}`}
        variant="primary"
        isLoading={bulkSending}
      />

      <ProgressModal
        isOpen={showProgress}
        items={bulkResults || []}
        onClose={() => setShowProgress(false)}
        onRetryFailed={handleRetryFailed}
      />
    </div>
  );
}
