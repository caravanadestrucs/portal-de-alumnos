import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./index', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { pages: [], total: 0 } }),
    post: vi.fn().mockResolvedValue({ data: { page: { id: 1 } } }),
    put: vi.fn().mockResolvedValue({ data: { page: { id: 1 } } }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

import api from './index';
import * as wikiApi from './wiki';

describe('wiki api', () => {
  beforeEach(() => vi.clearAllMocks());

  it('expone funciones CRUD + history + attachments', () => {
    expect(typeof wikiApi.getWikiPages).toBe('function');
    expect(typeof wikiApi.getWikiPage).toBe('function');
    expect(typeof wikiApi.createWikiPage).toBe('function');
    expect(typeof wikiApi.updateWikiPage).toBe('function');
    expect(typeof wikiApi.deleteWikiPage).toBe('function');
    expect(typeof wikiApi.getWikiHistory).toBe('function');
    expect(typeof wikiApi.uploadAttachment).toBe('function');
    expect(typeof wikiApi.listAttachments).toBe('function');
  });

  it('getWikiPages GET /wiki/pages con filtros sede_id, slug, search', async () => {
    await wikiApi.getWikiPages({ sede_id: 1, slug: 'guia', search: 'test' });
    expect(api.get).toHaveBeenCalled();
    const args = api.get.mock.calls[0];
    expect(args[0]).toMatch(/\/wiki\/pages/);
    const forwarded = JSON.stringify(args);
    expect(forwarded).toContain('1');
  });

  it('getWikiPage GET /wiki/pages/:id', async () => {
    await wikiApi.getWikiPage(7);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages/7'));
  });

  it('createWikiPage POST /wiki/pages con {sede_id,slug,title,body_markdown}', async () => {
    await wikiApi.createWikiPage({ sede_id: 1, slug: 'guia', title: 'Guia', body_markdown: '# Hola' });
    expect(api.post).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages'), expect.objectContaining({ slug: 'guia', title: 'Guia' }));
  });

  it('updateWikiPage PUT /wiki/pages/:id con body_markdown', async () => {
    await wikiApi.updateWikiPage(7, { title: 'New', body_markdown: 'updated' });
    expect(api.put).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages/7'), expect.objectContaining({ body_markdown: 'updated' }));
  });

  it('deleteWikiPage DELETE /wiki/pages/:id', async () => {
    await wikiApi.deleteWikiPage(7);
    expect(api.delete).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages/7'));
  });

  it('getWikiHistory GET /wiki/pages/:id/history', async () => {
    await wikiApi.getWikiHistory(7);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages/7/history'));
  });

  it('uploadAttachment POST multipart /wiki/pages/:id/attachments', async () => {
    const fakeFile = new File(['hello'], 'manual.pdf', { type: 'application/pdf' });
    await wikiApi.uploadAttachment(7, fakeFile);
    expect(api.post).toHaveBeenCalled();
    const url = api.post.mock.calls[0][0];
    expect(url).toMatch(/\/wiki\/pages\/7\/attachments/);
  });

  it('listAttachments GET /wiki/pages/:id/attachments', async () => {
    await wikiApi.listAttachments(7);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/wiki/pages/7/attachments'));
  });
});
