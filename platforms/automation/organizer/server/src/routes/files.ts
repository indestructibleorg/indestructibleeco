/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: files-route
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Files API Routes
 */

import { Router } from 'express';
import { DatabaseService } from '../services/database';
import { File } from '../types';
import { promises as fs } from 'fs';
import path from 'path';

const router = Router();
const dbService = new DatabaseService();

/**
 * GET /api/files - Get all files
 */
router.get('/', async (_req, res) => {
  try {
    const files = await dbService.getFiles();
    res.json(files);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve files' });
  }
});

/**
 * GET /api/files/export - Export all files in chunks
 */
router.get('/export', async (req, res) => {
  try {
    const mode = String(req.query.mode || '').toLowerCase();
    if (mode !== 'all') {
      return res.status(400).json({ error: 'mode=all is required for export' });
    }

    const chunkSize = Number.parseInt(String(req.query.chunkSize || '100'), 10);
    const offset = Number.parseInt(String(req.query.offset || '0'), 10);
    const safeChunkSize = Number.isNaN(chunkSize) ? 100 : Math.max(1, chunkSize);
    const safeOffset = Number.isNaN(offset) ? 0 : Math.max(0, offset);

    const chunk = await dbService.getFilesChunked(safeChunkSize, safeOffset);
    await appendAuditEvent({
      eventType: 'files_export_chunk',
      timestamp: new Date().toISOString(),
      metadata: {
        mode: 'all',
        chunkSize: safeChunkSize,
        offset: safeOffset,
        total: chunk.total,
        returned: chunk.files.length
      }
    });
    res.json({
      mode: 'all',
      chunkSize: safeChunkSize,
      offset: safeOffset,
      total: chunk.total,
      files: chunk.files,
      hasMore: safeOffset + safeChunkSize < chunk.total
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to export files' });
  }
});

async function appendAuditEvent(event: {
  eventType: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}): Promise<void> {
  const eventPath = path.resolve(__dirname, '../../../.governance/event-stream.jsonl');
  const eventLine = JSON.stringify({ source: 'files-route', ...event }) + '\n';
  await fs.mkdir(path.dirname(eventPath), { recursive: true });
  await fs.appendFile(eventPath, eventLine, 'utf-8');
}

/**
 * GET /api/files/:id - Get a specific file
 */
router.get('/:id', async (req, res) => {
  try {
    const files = await dbService.getFiles();
    const file = files.find(f => f.id === req.params.id);

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    res.json(file);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve file' });
  }
});

/**
 * POST /api/files - Add a new file
 */
router.post('/', async (req, res) => {
  try {
    const fileData: File = req.body;
    const files = await dbService.getFiles();
    files.push(fileData);
    await dbService.saveFiles(files);
    
    res.status(201).json(fileData);
  } catch (error) {
    res.status(500).json({ error: 'Failed to add file' });
  }
});

/**
 * DELETE /api/files/:id - Delete a file
 */
router.delete('/:id', async (req, res) => {
  try {
    const files = await dbService.getFiles();
    const filteredFiles = files.filter(f => f.id !== req.params.id);
    await dbService.saveFiles(filteredFiles);
    
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete file' });
  }
});

export default router;
