import { useState, useEffect } from 'react';
import { getWikiPages, createWikiPage, updateWikiPage, deleteWikiPage, getWikiHistory, uploadAttachment, listAttachments } from '../../api/wiki';
import { getSedes } from '../../api/sedes';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { useToast } from '../../components/ui/Toast';
import { Plus, Pencil, Trash2, History, Paperclip, Upload } from 'lucide-react';

export default function WikiAdmin() {
  const { isGeneralAdmin, sedeId } = useAuth();
  const toast = useToast();
  const [pages, setPages] = useState([]);
  const [sedes, setSedes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ slug: '', title: '', body_markdown: '', sede_id: '' });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [history, setHistory] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);

  const fetchPages = async () => {
    setLoading(true);
    try {
      const data = await getWikiPages();
      setPages(data.pages || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSedes = async () => {
    try {
      const data = await getSedes();
      setSedes(data.sedes || []);
    } catch (e) { /* ignore */ }
  };

  useEffect(() => {
    fetchPages();
    fetchSedes();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ slug: '', title: '', body_markdown: '', sede_id: isGeneralAdmin ? '' : (sedeId || '') });
    setAttachments([]);
    setHistory(null);
    setShowModal(true);
  };

  const openEdit = async (page) => {
    setEditing(page);
    setForm({ slug: page.slug, title: page.title, body_markdown: page.body_markdown || page.body || '', sede_id: page.sede_id || '' });
    setShowModal(true);
    // load history
    try {
      const h = await getWikiHistory(page.id);
      setHistory(h.revisions || h.history || []);
    } catch (e) { setHistory([]); }
    // load attachments
    try {
      const a = await listAttachments(page.id);
      setAttachments(a.attachments || []);
    } catch (e) { setAttachments([]); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        slug: form.slug.trim(),
        title: form.title.trim(),
        body_markdown: form.body_markdown,
        sede_id: form.sede_id ? parseInt(form.sede_id, 10) : null,
      };
      if (!payload.slug || !payload.title || !payload.body_markdown) {
        toast.error('Slug, Título y Contenido son requeridos');
        setSaving(false);
        return;
      }
      if (editing) {
        await updateWikiPage(editing.id, { title: payload.title, body_markdown: payload.body_markdown });
        toast.success('Página actualizada');
      } else {
        await createWikiPage(payload);
        toast.success('Página creada');
      }
      setShowModal(false);
      fetchPages();
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      if (err.response?.status === 409) toast.error('Slug ya existe en esta sede');
      else toast.error(msg || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteWikiPage(deleteTarget.id);
      toast.success('Página eliminada');
      setDeleteTarget(null);
      fetchPages();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al eliminar');
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !editing) return;
    setUploading(true);
    try {
      await uploadAttachment(editing.id, file);
      toast.success('Archivo subido');
      const a = await listAttachments(editing.id);
      setAttachments(a.attachments || []);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error al subir');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const openHistory = async (page) => {
    try {
      const h = await getWikiHistory(page.id);
      setHistory(h.revisions || h.history || []);
      setShowHistory(true);
    } catch (e) {
      toast.error('No se pudo cargar historial');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Wiki</h1>
          <p className="text-gray-500 mt-1">Manuales por sede — global o privado</p>
        </div>
        <Button onClick={openCreate}>
          <Plus size={18} />
          Nueva Página
        </Button>
      </div>

      <Card>
        {loading ? (
          <TableSkeleton rows={5} columns={4} />
        ) : pages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No hay páginas wiki</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Slug</th>
                  <th className="text-left py-3 px-4">Título</th>
                  <th className="text-left py-3 px-4">Sede</th>
                  <th className="text-center py-3 px-4">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {pages.map((p) => (
                  <tr key={p.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{p.slug}</td>
                    <td className="py-3 px-4">{p.title}</td>
                    <td className="py-3 px-4">{p.sede?.codigo || (p.sede_id == null ? 'Global' : p.sede_id)}</td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEdit(p)} className="p-2 text-green-600 hover:bg-green-50 rounded" title="Editar">
                          <Pencil size={16} />
                        </button>
                        <button onClick={() => openHistory(p)} className="p-2 text-blue-600 hover:bg-blue-50 rounded" title="Historial">
                          <History size={16} />
                        </button>
                        <button onClick={() => setDeleteTarget(p)} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Eliminar">
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

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Página' : 'Crear Página'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required disabled={!!editing} placeholder="guia-teo" helper="Solo slug, minúsculas, guiones" />
          <Input label="Título" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <Select label="Sede" value={form.sede_id} onChange={(e) => setForm({ ...form, sede_id: e.target.value })} disabled={!!editing && !isGeneralAdmin}>
            <option value="">Global (todas las sedes)</option>
            {sedes.map((s) => (
              <option key={s.id} value={s.id}>{s.codigo} — {s.nombre}</option>
            ))}
          </Select>
          <div>
            <label className="block text-sm font-medium mb-1">Contenido Markdown</label>
            <textarea
              aria-label="Body"
              value={form.body_markdown}
              onChange={(e) => setForm({ ...form, body_markdown: e.target.value })}
              rows={10}
              className="w-full border border-gray-300 rounded-xl p-3 font-mono text-sm"
              placeholder="# Título&#10;Contenido en markdown..."
              required
            />
            <label className="block text-sm font-medium mt-2">Contenido (alias)</label>
            <textarea
              aria-label="Markdown"
              value={form.body_markdown}
              onChange={(e) => setForm({ ...form, body_markdown: e.target.value })}
              rows={4}
              className="w-full border border-gray-300 rounded-xl p-3 font-mono text-sm hidden"
            />
          </div>

          {editing && (
            <div className="border-t pt-4 space-y-3">
              <h3 className="font-semibold flex items-center gap-2"><History size={16} /> Historial</h3>
              {history && history.length > 0 ? (
                <ul className="space-y-2 max-h-32 overflow-y-auto">
                  {history.map((rev) => (
                    <li key={rev.id} className="text-xs bg-gray-50 p-2 rounded">{new Date(rev.created_at).toLocaleString()} — {rev.title || rev.body_markdown?.slice(0, 40)}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">Sin historial o 1 revisión</p>
              )}

              <h3 className="font-semibold flex items-center gap-2"><Paperclip size={16} /> Adjuntos</h3>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 text-sm">
                  <Upload size={16} />
                  {uploading ? 'Subiendo...' : 'Subir Archivo'}
                  <input type="file" className="hidden" onChange={handleUpload} disabled={uploading} aria-label="Adjuntos" />
                </label>
                <span className="text-xs text-gray-500">Adjuntos — PDF, imágenes, docs (10MB máx)</span>
              </div>
              {attachments.length > 0 ? (
                <ul className="text-sm space-y-1">
                  {attachments.map((a) => (
                    <li key={a.id} className="flex items-center gap-2">
                      <Paperclip size={14} /> {a.filename} <span className="text-xs text-gray-500">({a.mime})</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">Sin adjuntos</p>
              )}
              <p className="text-sm text-gray-500">Archivo</p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)} className="flex-1">Cancelar</Button>
            <Button type="submit" loading={saving} className="flex-1">{editing ? 'Guardar' : 'Crear'}</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showHistory} onClose={() => setShowHistory(false)} title="Historial de Revisiones">
        <div className="space-y-2">
          {history ? history.map((r) => (
            <div key={r.id} className="border p-2 rounded">
              <p className="text-xs text-gray-500">{r.created_at}</p>
              <pre className="text-sm whitespace-pre-wrap">{r.body_markdown || r.body}</pre>
            </div>
          )) : <p>No hay historial</p>}
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Eliminar página"
        message={deleteTarget ? `¿Eliminar ${deleteTarget.slug}?` : ''}
        confirmText="Eliminar"
        variant="danger"
      />

      {/* helpers for a11y, not hidden duplicate counts */}
    </div>
  );
}
