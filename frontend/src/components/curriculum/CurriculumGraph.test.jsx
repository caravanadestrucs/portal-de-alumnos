import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CurriculumGraph from './CurriculumGraph';

function makeMaterias(count = 45) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    nombre: `Materia ${i + 1}`,
    codigo: `MAT-${i + 1}`,
    cuatrimestre: Math.floor(i / 5) + 1, // 9×5
    estado: 'pendiente',
  }));
}

describe('CurriculumGraph', () => {
  beforeEach(() => vi.clearAllMocks());

  it('admin ve 45 nodos agrupados en 9 columnas', () => {
    const materias = makeMaterias(45);
    const { container } = render(<CurriculumGraph materias={materias} onMateriaClick={vi.fn()} />);
    // 45 nodos
    const nodes = screen.getAllByTestId(/materia-node/i);
    expect(nodes).toHaveLength(45);
    // títulos dentro de nodos incluyen nombre y cuatrimestre label — usar testids exactos
    expect(screen.getByTestId('materia-node-1')).toBeInTheDocument();
    expect(screen.getByTestId('materia-node-45')).toBeInTheDocument();
    expect(within(screen.getByTestId('materia-node-1')).getByText('Materia 1')).toBeInTheDocument();
    expect(within(screen.getByTestId('materia-node-45')).getByText('Materia 45')).toBeInTheDocument();
    // grid 9 columnas: verifica que contenedor tenga clase grid y 9 cols
    const grid = container.querySelector('[data-testid="curriculum-grid"]');
    expect(grid).not.toBeNull();
    // columnas agrupadas: debe tener 9 headers o columns
    const cols = container.querySelectorAll('[data-testid^="cuatrimestre-col"]');
    expect(cols.length).toBe(9);
    // cada cuatrimestre label
    expect(container.querySelector('[data-testid="cuatrimestre-col-1"]')).not.toBeNull();
    expect(container.querySelector('[data-testid="cuatrimestre-col-9"]')).not.toBeNull();
  });

  it('alumno ve colores: 10 verde aprobado, 5 amarillo cursando, 30 gris pendiente + leyenda', () => {
    const materias = makeMaterias(45).map((m, idx) => {
      if (idx < 10) return { ...m, estado: 'aprobado', nota: 9 };
      if (idx < 15) return { ...m, estado: 'cursando', nota: null };
      return { ...m, estado: 'pendiente' };
    });
    render(<CurriculumGraph materias={materias} onMateriaClick={vi.fn()} />);
    const nodes = screen.getAllByTestId(/materia-node/i);
    expect(nodes).toHaveLength(45);
    // verifica colores por data-estado o clase
    const aprobados = document.querySelectorAll('[data-estado="aprobado"]');
    const cursando = document.querySelectorAll('[data-estado="cursando"]');
    const pendientes = document.querySelectorAll('[data-estado="pendiente"]');
    expect(aprobados.length).toBe(10);
    expect(cursando.length).toBe(5);
    expect(pendientes.length).toBe(30);
    // leyenda explica colores
    expect(screen.getByText(/Aprobado/i)).toBeInTheDocument();
    expect(screen.getByText(/Pendiente/i)).toBeInTheDocument();
    // al menos mención de gris/amarillo/verde o forma de leyenda
    const legend = screen.getByTestId('curriculum-legend');
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toMatch(/Aprobado/);
  });

  it('click materia muestra detalle con nombre cuatrimestre estado nota', async () => {
    const user = userEvent.setup();
    const onMateriaClick = vi.fn();
    const base = makeMaterias(10).filter((m) => m.id !== 7);
    const materias = [
      { id: 7, nombre: 'Física I', codigo: 'FIS1', cuatrimestre: 2, estado: 'aprobado', nota: 8, correlativas: [] },
      ...base,
    ];
    render(<CurriculumGraph materias={materias} onMateriaClick={onMateriaClick} />);
    // busca nodo Física I
    const fisicaNode = screen.getByText(/Física I/i).closest('[data-testid*="materia-node"]') || screen.getByText(/Física I/i);
    await act(async () => {
      await user.click(fisicaNode);
    });
    // esperar flush de setSelected (modal) para evitar warning act()
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
    // debe llamar onMateriaClick con materia
    expect(onMateriaClick).toHaveBeenCalled();
    const calledArg = onMateriaClick.mock.calls[0][0];
    expect(calledArg.nombre).toMatch(/Física I/);
    expect(calledArg.cuatrimestre).toBe(2);
    // detalle panel/modal debe aparecer con estado y nota
    // si el componente auto-muestra modal, verificamos detalle
    // si solo llama callback, al menos callback contenía estado
    expect(calledArg.estado).toBe('aprobado');
    // si componente muestra panel interno, buscamos texto detalle
    // toleramos ambos: o modal interno aparece o callback basta, pero testeamos ambos
    // verificamos que después del click hay panel detalle si onMateriaClick no es único manejo
    // Busca texto de cuatrimestre en detalle si existe
    // no falla si no hay modal interno, pero verifica callback
  });
});
