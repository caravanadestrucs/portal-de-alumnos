import { useState, useEffect, useMemo } from 'react';
import { useFetch } from '../../hooks/useFetch';
import * as alumnosApi from '../../api/alumnos';
import * as practicasApi from '../../api/practicas';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import { Search, Save, X, Edit2, Check, Clock } from 'lucide-react';

export default function AdminRequisitos() {
  const { data: alumnos, refetch } = useFetch(alumnosApi.getAlumnos);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAlumno, setSelectedAlumno] = useState(null);
  const [practicas, setPracticas] = useState([]);
  const [loadingPracticas, setLoadingPracticas] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editando, setEditando] = useState(false);

  // Form data
  const [formData, setFormData] = useState({
    nombre: '', apellido_paterno: '', apellido_materno: '', email: '',
    servicio_social: false, examen_idiomas: false, credenciales_completas: false, documentacion_completa: false,
  });
  const [practica1, setPractica1] = useState({ nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });
  const [practica2, setPractica2] = useState({ nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });

  // Filtrar alumnos
  const filteredAlumnos = useMemo(() => {
    if (!alumnos || !searchTerm) return [];
    const term = searchTerm.toLowerCase();
    return alumnos.filter(a => 
      (a.numero_control || '').toLowerCase().includes(term) ||
      (a.nombre || '').toLowerCase().includes(term) ||
      (a.apellido_paterno || '').toLowerCase().includes(term)
    ).slice(0, 10);
  }, [alumnos, searchTerm]);

  const loadAlumno = async (alumno) => {
    setSelectedAlumno(alumno);
    setEditando(false);
    setFormData({
      nombre: alumno.nombre || '',
      apellido_paterno: alumno.apellido_paterno || '',
      apellido_materno: alumno.apellido_materno || '',
      email: alumno.email || '',
      servicio_social: alumno.servicio_social || false,
      examen_idiomas: alumno.examen_idiomas || false,
      credenciales_completas: alumno.credenciales_completas || false,
      documentacion_completa: alumno.documentacion_completa || false,
    });

    setLoadingPracticas(true);
    try {
      const data = await practicasApi.getPracticasByAlumno(alumno.id);
      const p1 = data.find(p => p.numero_practica === 1);
      const p2 = data.find(p => p.numero_practica === 2);
      setPractica1(p1 ? { nombre_empresa: p1.nombre_empresa || '', horas: p1.horas || 480, fecha_inicio: p1.fecha_inicio || '', fecha_fin: p1.fecha_fin || '', estado: p1.estado || 'pendiente' } : { nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });
      setPractica2(p2 ? { nombre_empresa: p2.nombre_empresa || '', horas: p2.horas || 480, fecha_inicio: p2.fecha_inicio || '', fecha_fin: p2.fecha_fin || '', estado: p2.estado || 'pendiente' } : { nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });
    } catch (error) {
      setPractica1({ nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });
      setPractica2({ nombre_empresa: '', horas: 480, fecha_inicio: '', fecha_fin: '', estado: 'pendiente' });
    } finally {
      setLoadingPracticas(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Guardar datos del alumno
      await alumnosApi.updateAlumno(selectedAlumno.id, {
        nombre: formData.nombre,
        apellido_paterno: formData.apellido_paterno,
        apellido_materno: formData.apellido_materno,
        email: formData.email,
        servicio_social: formData.servicio_social,
        examen_idiomas: formData.examen_idiomas,
        credenciales_completas: formData.credenciales_completas,
        documentacion_completa: formData.documentacion_completa,
      });

      // Guardar práctica 1
      const p1Exist = (await practicasApi.getPracticasByAlumno(selectedAlumno.id)).find(p => p.numero_practica === 1);
      if (p1Exist) {
        await practicasApi.updatePractica(p1Exist.id, practica1);
      } else if (practica1.nombre_empresa) {
        await practicasApi.createPractica({ ...practica1, numero_practica: 1, alumno_id: selectedAlumno.id });
      }

      // Guardar práctica 2
      const p2Exist = (await practicasApi.getPracticasByAlumno(selectedAlumno.id)).find(p => p.numero_practica === 2);
      if (p2Exist) {
        await practicasApi.updatePractica(p2Exist.id, practica2);
      } else if (practica2.nombre_empresa) {
        await practicasApi.createPractica({ ...practica2, numero_practica: 2, alumno_id: selectedAlumno.id });
      }

      setEditando(false);
      refetch();
      alert('Datos guardados exitosamente');
    } catch (error) {
      alert(error.response?.data?.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Requisitos de Titulación</h1>
        <p className="text-gray-500 mt-1">Editar datos del alumno, requisitos y prácticas profesionales</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Buscador */}
        <Card className="lg:col-span-1">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Buscar Alumno</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Matrícula o nombre..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl input-glass"
            />
          </div>
          {searchTerm && (
            <div className="mt-2 max-h-64 overflow-y-auto space-y-1">
              {filteredAlumnos.length === 0 ? (
                <p className="text-sm text-gray-500 p-2">Sin resultados</p>
              ) : (
                filteredAlumnos.map((alumno) => (
                  <button
                    key={alumno.id}
                    onClick={() => { loadAlumno(alumno); setSearchTerm(''); }}
                    className={`w-full text-left p-2 rounded-lg ${selectedAlumno?.id === alumno.id ? 'bg-primary-50 border border-primary-500' : 'hover:bg-gray-50 border border-transparent'}`}
                  >
                    <p className="font-medium text-sm text-gray-800">{alumno.nombre} {alumno.apellido_paterno}</p>
                    <p className="text-xs text-gray-500">{alumno.numero_control}</p>
                  </button>
                ))
              )}
            </div>
          )}
        </Card>

        {/* Formulario */}
        {selectedAlumno ? (
          <div className="lg:col-span-3 space-y-6">
            {/* Datos Personales */}
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-800">Datos Personales</h2>
                {!editando ? (
                  <Button size="sm" variant="secondary" onClick={() => setEditando(true)}>
                    <Edit2 size={16} className="mr-1" /> Editar
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => setEditando(false)}>
                      <X size={16} className="mr-1" /> Cancelar
                    </Button>
                    <Button size="sm" onClick={handleSave} loading={saving}>
                      <Check size={16} className="mr-1" /> Guardar
                    </Button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input label="Nombre" value={formData.nombre} onChange={(e) => setFormData({...formData, nombre: e.target.value})} disabled={!editando} />
                <Input label="Apellido Paterno" value={formData.apellido_paterno} onChange={(e) => setFormData({...formData, apellido_paterno: e.target.value})} disabled={!editando} />
                <Input label="Apellido Materno" value={formData.apellido_materno || ''} onChange={(e) => setFormData({...formData, apellido_materno: e.target.value})} disabled={!editando} />
                <Input label="Email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} disabled={!editando} />
              </div>
              <div className="mt-2 text-sm text-gray-500">
                <p>Matrícula: <strong>{selectedAlumno.numero_control}</strong></p>
                <p>Carrera: <strong>{selectedAlumno.carrera?.nombre || '-'}</strong></p>
              </div>
            </Card>

            {/* Requisitos de Titulación */}
            <Card>
              <h2 className="text-lg font-bold text-gray-800 mb-4">Requisitos de Titulación</h2>
              <div className="grid grid-cols-2 gap-4">
                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input type="checkbox" checked={formData.servicio_social} onChange={(e) => setFormData({...formData, servicio_social: e.target.checked})} disabled={!editando} className="w-5 h-5" />
                  <span className={formData.servicio_social ? 'text-green-700' : 'text-gray-600'}>Servicio Social</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input type="checkbox" checked={formData.examen_idiomas} onChange={(e) => setFormData({...formData, examen_idiomas: e.target.checked})} disabled={!editando} className="w-5 h-5" />
                  <span className={formData.examen_idiomas ? 'text-green-700' : 'text-gray-600'}>Examen de Idiomas</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input type="checkbox" checked={formData.credenciales_completas} onChange={(e) => setFormData({...formData, credenciales_completas: e.target.checked})} disabled={!editando} className="w-5 h-5" />
                  <span className={formData.credenciales_completas ? 'text-green-700' : 'text-gray-600'}>Credenciales Completas</span>
                </label>
                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input type="checkbox" checked={formData.documentacion_completa} onChange={(e) => setFormData({...formData, documentacion_completa: e.target.checked})} disabled={!editando} className="w-5 h-5" />
                  <span className={formData.documentacion_completa ? 'text-green-700' : 'text-gray-600'}>Documentación Completa</span>
                </label>
              </div>
            </Card>

            {/* Prácticas Profesionales */}
            <Card>
              <h2 className="text-lg font-bold text-gray-800 mb-4">Prácticas Profesionales</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Práctica 1 */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-gray-800">Práctica 1</h3>
                    <Badge variant={practica1.estado === 'completada' ? 'success' : practica1.estado === 'en_curso' ? 'info' : 'warning'}>
                      {practica1.estado || 'Sin registrar'}
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    <Input label="Empresa" value={practica1.nombre_empresa} onChange={(e) => setPractica1({...practica1, nombre_empresa: e.target.value})} disabled={!editando} />
                    <Input label="Horas" type="number" value={practica1.horas} onChange={(e) => setPractica1({...practica1, horas: parseInt(e.target.value) || 0})} disabled={!editando} />
                    <div className="grid grid-cols-2 gap-2">
                      <Input label="Fecha Inicio" type="date" value={practica1.fecha_inicio} onChange={(e) => setPractica1({...practica1, fecha_inicio: e.target.value})} disabled={!editando} />
                      <Input label="Fecha Fin" type="date" value={practica1.fecha_fin} onChange={(e) => setPractica1({...practica1, fecha_fin: e.target.value})} disabled={!editando} />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                      <select value={practica1.estado} onChange={(e) => setPractica1({...practica1, estado: e.target.value})} disabled={!editando} className="w-full px-4 py-2.5 rounded-xl input-glass">
                        <option value="pendiente">Pendiente</option>
                        <option value="en_curso">En Curso</option>
                        <option value="completada">Completada</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Práctica 2 */}
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-gray-800">Práctica 2</h3>
                    <Badge variant={practica2.estado === 'completada' ? 'success' : practica2.estado === 'en_curso' ? 'info' : 'warning'}>
                      {practica2.estado || 'Sin registrar'}
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    <Input label="Empresa" value={practica2.nombre_empresa} onChange={(e) => setPractica2({...practica2, nombre_empresa: e.target.value})} disabled={!editando} />
                    <Input label="Horas" type="number" value={practica2.horas} onChange={(e) => setPractica2({...practica2, horas: parseInt(e.target.value) || 0})} disabled={!editando} />
                    <div className="grid grid-cols-2 gap-2">
                      <Input label="Fecha Inicio" type="date" value={practica2.fecha_inicio} onChange={(e) => setPractica2({...practica2, fecha_inicio: e.target.value})} disabled={!editando} />
                      <Input label="Fecha Fin" type="date" value={practica2.fecha_fin} onChange={(e) => setPractica2({...practica2, fecha_fin: e.target.value})} disabled={!editando} />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                      <select value={practica2.estado} onChange={(e) => setPractica2({...practica2, estado: e.target.value})} disabled={!editando} className="w-full px-4 py-2.5 rounded-xl input-glass">
                        <option value="pendiente">Pendiente</option>
                        <option value="en_curso">En Curso</option>
                        <option value="completada">Completada</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <div className="lg:col-span-3">
            <Card className="text-center py-16">
              <Search size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Busca y selecciona un alumno para editar</p>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}