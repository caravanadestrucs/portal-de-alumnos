import { useState, useMemo } from 'react';
import { tokens } from '../ui/tokens';
import { getEffectiveGrade } from '../../utils/grades';
import { X } from 'lucide-react';

const ESTAD_COLORS = {
  aprobado: tokens.colors.success,
  reprobado: tokens.colors.danger,
  cursando: tokens.colors.warning,
  regular: tokens.colors.warning,
  pendiente: '#9ca3af',
};

function normalizeEstado(materia) {
  if (materia?.estado) {
    const e = String(materia.estado).toLowerCase().trim();
    if (e.includes('aprob')) return 'aprobado';
    if (e.includes('reprob')) return 'reprobado';
    if (e.includes('curs') || e.includes('regular')) return 'cursando';
    if (e.includes('pend')) return 'pendiente';
    // fallthrough for exact
    if (['aprobado', 'pendiente', 'cursando', 'regular', 'reprobado'].includes(e)) return e;
  }
  // derive from grade if available
  const cal = materia;
  // try getEffectiveGrade if shape matches calificacion
  if (cal && (cal.calificacion_final != null || cal.final != null || cal.nota != null)) {
    const notaRaw = cal.nota ?? cal.calificacion_final ?? cal.final ?? null;
    if (notaRaw != null && notaRaw !== '' && Number(notaRaw) !== 0 && !isNaN(Number(notaRaw))) {
      return Number(notaRaw) >= 8 ? 'aprobado' : 'reprobado';
    }
  }
  if (materia?.nota != null && materia.nota !== '' && Number(materia.nota) !== 0 && !isNaN(Number(materia.nota))) {
    return Number(materia.nota) >= 8 ? 'aprobado' : 'reprobado';
  }
  return 'pendiente';
}

function getNodeStyle(estado) {
  const color = ESTAD_COLORS[estado] || ESTAD_COLORS.pendiente;
  // approved etc get solid bg, pendiente gets light gray bg
  if (estado === 'pendiente') {
    return { backgroundColor: '#f3f4f6', borderColor: '#e5e7eb', color: '#6b7280', borderWidth: '1px' };
  }
  return { backgroundColor: color, color: '#ffffff', borderColor: color, borderWidth: '1px' };
}

export function getMateriaEstado(materia) {
  return normalizeEstado(materia);
}

export default function CurriculumGraph({ materias = [], onMateriaClick }) {
  const [selected, setSelected] = useState(null);

  const grouped = useMemo(() => {
    const g = {};
    for (let i = 1; i <= 9; i++) g[i] = [];
    for (const m of materias) {
      const c = Number(m.cuatrimestre) || 1;
      const key = Math.min(Math.max(c, 1), 9);
      g[key].push(m);
    }
    return g;
  }, [materias]);

  const handleClick = (m) => {
    setSelected(m);
    onMateriaClick?.(m);
  };

  if (!materias || materias.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No hay materias para mostrar
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        data-testid="curriculum-grid"
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-9 gap-3"
      >
        {Array.from({ length: 9 }, (_, idx) => {
          const cuatri = idx + 1;
          const list = grouped[cuatri] || [];
          return (
            <div
              key={cuatri}
              data-testid={`cuatrimestre-col-${cuatri}`}
              className="space-y-2"
            >
              <div className="text-center">
                <span className="text-xs font-bold text-gray-600 uppercase tracking-wide">
                  C{cuatri}
                </span>
                <div className="text-[10px] text-gray-400">{list.length} mat.</div>
              </div>
              <div className="space-y-1.5">
                {list.map((m) => {
                  const estado = normalizeEstado(m);
                  const style = getNodeStyle(estado);
                  return (
                    <button
                      key={m.id}
                      data-testid={`materia-node-${m.id}`}
                      data-estado={estado}
                      onClick={() => handleClick(m)}
                      className="w-full text-left px-2 py-2 rounded-lg text-xs font-medium transition-all hover:scale-[1.02] hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500 border"
                      style={style}
                      title={`${m.nombre} — C${m.cuatrimestre}`}
                    >
                      <div className="truncate leading-tight">{m.nombre}</div>
                      <div className="text-[10px] opacity-80 truncate">
                        {m.codigo ? `${m.codigo} · ` : ''}C{m.cuatrimestre}
                      </div>
                    </button>
                  );
                })}
                {list.length === 0 && (
                  <div className="text-[11px] text-gray-300 text-center py-2">—</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div
        data-testid="curriculum-legend"
        className="flex flex-wrap items-center gap-4 text-xs text-gray-600 border-t border-gray-100 pt-3"
      >
        <span className="font-semibold">Leyenda:</span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: ESTAD_COLORS.aprobado }} aria-hidden="true" />
          Aprobado
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: ESTAD_COLORS.cursando }} aria-hidden="true" />
          Cursando / Regular
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: ESTAD_COLORS.pendiente, border: '1px solid #e5e7eb' }} aria-hidden="true" />
          Pendiente
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: ESTAD_COLORS.reprobado }} aria-hidden="true" />
          Reprobado
        </span>
      </div>

      {selected && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelected(null)} aria-hidden="true" />
          <div role="dialog" aria-modal="true" aria-labelledby="materia-detail-title" className="relative w-full max-w-md glass rounded-2xl shadow-xl p-6">
            <button
              onClick={() => setSelected(null)}
              aria-label="Cerrar detalle"
              className="absolute top-3 right-3 p-2 rounded-lg hover:bg-gray-100"
            >
              <X size={16} className="text-gray-500" />
            </button>
            <h3 id="materia-detail-title" className="text-lg font-bold text-gray-800 pr-6">
              {selected.nombre}
            </h3>
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Cuatrimestre</span>
                <span className="font-medium">{selected.cuatrimestre}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Estado</span>
                <span className="font-medium capitalize">{normalizeEstado(selected)}</span>
              </div>
              {selected.nota != null && selected.nota !== '' && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Nota</span>
                  <span className="font-bold">{selected.nota}</span>
                </div>
              )}
              {selected.codigo && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Código</span>
                  <span className="font-mono text-xs">{selected.codigo}</span>
                </div>
              )}
              {selected.correlativas && selected.correlativas.length > 0 && (
                <div>
                  <span className="text-gray-500 text-xs">Correlativas</span>
                  <p className="text-xs mt-1">{selected.correlativas.join(', ')}</p>
                </div>
              )}
              {selected.calificacion_final != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Calificación</span>
                  <span className="font-bold">{getEffectiveGrade(selected).value ?? '-'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
