/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: database-service
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Database Service
 */

import { File, Rule, Task } from '../types';
import { promises as fs } from 'fs';
import path from 'path';

export class DatabaseService {
  private dbPath: string;

  constructor(dbPath: string = './data') {
    this.dbPath = dbPath;
  }

  /**
   * Initialize database
   */
  async initialize(): Promise<void> {
    await fs.mkdir(this.dbPath, { recursive: true });
    await this.ensureDataFiles();
  }

  /**
   * Ensure data files exist
   */
  private async ensureDataFiles(): Promise<void> {
    const filesPath = path.join(this.dbPath, 'files.json');
    const rulesPath = path.join(this.dbPath, 'rules.json');
    const tasksPath = path.join(this.dbPath, 'tasks.json');

    for (const filePath of [filesPath, rulesPath, tasksPath]) {
      try {
        await fs.access(filePath);
      } catch {
        await fs.writeFile(filePath, '[]', 'utf-8');
      }
    }
  }

  /**
   * Get all files
   */
  async getFiles(): Promise<File[]> {
    const filePath = path.join(this.dbPath, 'files.json');
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * Get files in chunks
   */
  async getFilesChunked(chunkSize: number = 100, offset: number = 0): Promise<{
    files: File[];
    total: number;
  }> {
    const files = await this.getFiles();
    const safeOffset = Math.max(0, offset);
    const safeChunkSize = Math.max(1, chunkSize);
    return {
      files: files.slice(safeOffset, safeOffset + safeChunkSize),
      total: files.length
    };
  }

  /**
   * Save files
   */
  async saveFiles(files: File[]): Promise<void> {
    const filePath = path.join(this.dbPath, 'files.json');
    await fs.writeFile(filePath, JSON.stringify(files, null, 2), 'utf-8');
  }

  /**
   * Get all rules
   */
  async getRules(): Promise<Rule[]> {
    const filePath = path.join(this.dbPath, 'rules.json');
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * Save rules
   */
  async saveRules(rules: Rule[]): Promise<void> {
    const filePath = path.join(this.dbPath, 'rules.json');
    await fs.writeFile(filePath, JSON.stringify(rules, null, 2), 'utf-8');
  }

  /**
   * Get all tasks
   */
  async getTasks(): Promise<Task[]> {
    const filePath = path.join(this.dbPath, 'tasks.json');
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * Save tasks
   */
  async saveTasks(tasks: Task[]): Promise<void> {
    const filePath = path.join(this.dbPath, 'tasks.json');
    await fs.writeFile(filePath, JSON.stringify(tasks, null, 2), 'utf-8');
  }
}
