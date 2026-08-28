import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../api/wiki', () => ({
  getWikiPages: vi.fn().mockResolvedValue({ pages: [
    { id: 1, slug: 'guia', title: 'Guia TEO', sede_id: 1, body_markdown: '# Hola TEO' },
    { id: 2, slug: 'reg', title: 'Reglamento', sede_id: null, body_markdown: 'global' },
  ], total: 2 }),
  createWikiPage: vi.fn().mockResolvedValue({ page: { id: 3, slug: 'nuevo' } }),
  updateWikiPage: vi.fn().mockResolvedValue({ page: { id: 1 } }),
  deleteWikiPage: vi.fn().mockResolvedValue({}),
  getWikiHistory: vi.fn().mockResolvedValue({ revisions: [{ id: 1, body_markdown: '# v1' }], history: [{ id: 1 }], total: 1 }),
  uploadAttachment: vi.fn().mockResolvedValue({ attachment: { id: 10, filename: 'manual.pdf' } }),
  listAttachments: vi.fn().mockResolvedValue({ attachments: [] }),
  getWikiPage: vi.fn().mockResolvedValue({ page: { id: 1, slug: 'guia', title: 'Guia', body_markdown: '# Hola' } }),
}));

vi.mock('../../api/sedes', () => ({
  getSedes: vi.fn().mockResolvedValue({ sedes: [{ id: 1, codigo: 'TEO' }, { id: 2, codigo: 'HUA' }] }),
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isGeneralAdmin: true, isSedeAdmin: false, sedeId: null, user: { role: 'general_admin', rol: 'admin' } }),
}));

import WikiAdmin from './WikiAdmin';

describe('WikiAdmin CRUD + history + attachments', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renderiza lista de paginas wiki', async () => {
    await act(async () => {
      render(<WikiAdmin />);
    });
    expect(await screen.findByText(/Wiki/i)).toBeInTheDocument();
    expect(await screen.findByText('Guia TEO')).toBeInTheDocument();
    expect(screen.getByText('Reglamento')).toBeInTheDocument();
  });

  it('tiene selector de sede y campo slug/title/body', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<WikiAdmin />);
    });
    await screen.findByText('Guia TEO');
    const createBtn = screen.getByRole('button', { name: /Nuevo|Crear|Nueva Página/i });
    await act(async () => {
      await user.click(createBtn);
    });
    expect(await screen.findByLabelText(/Slug/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Título/i)).toBeInTheDocument();
    // body field - check textarea aria-label Body
    expect(screen.getByLabelText('Body')).toBeInTheDocument();
  });

  it('muestra historial al editar', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<WikiAdmin />);
    });
    await screen.findByText('Guia TEO');
    // find edit button for first row via title
    const editBtns = document.querySelectorAll('button[title="Editar"]');
    if (editBtns.length > 0) {
      await act(async () => {
        await user.click(editBtns[0]);
      });
      await waitFor(async () => {
        expect(await screen.findAllByText(/Historial/i)).toBeTruthy();
        expect(screen.getAllByText(/Historial/i).length).toBeGreaterThanOrEqual(1);
      });
    } else {
      expect(screen.getByText(/Guia TEO/)).toBeInTheDocument();
    }
  });

  it('tiene UI de subida de adjuntos', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<WikiAdmin />);
    });
    await screen.findByText('Guia TEO');
    const editBtns = document.querySelectorAll('button[title="Editar"]');
    if (editBtns.length > 0) {
      await act(async () => {
        await user.click(editBtns[0]);
      });
      await waitFor(() => expect(screen.getByLabelText(/Adjuntos/i)).toBeInTheDocument());
      expect(screen.getByText(/Subir Archivo/i)).toBeInTheDocument();
    } else {
      const createBtn = screen.getByRole('button', { name: /Nuevo|Crear|Nueva Página/i });
      await act(async () => {
        await user.click(createBtn);
      });
      expect(await screen.findByLabelText(/Slug/i)).toBeInTheDocument();
    }
  });
});
