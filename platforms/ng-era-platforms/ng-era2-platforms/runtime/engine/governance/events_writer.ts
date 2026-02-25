/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: event-stream
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Governance Event Writer
 * Maintains persistent governance event stream
 */

import { promises as fs } from 'fs';
import path from 'path';

export interface GovernanceEvent {
  id: string;
  type: 'validation' | 'compliance' | 'enforcement' | 'audit';
  timestamp: string;
  source: string;
  data: any;
}

export class GovernanceEventWriter {
  private eventLogPath: string;

  constructor(private workspace: string = process.cwd()) {
    this.eventLogPath = path.join(workspace, '.governance', 'event-stream.jsonl');
  }

  async writeEvents(events: GovernanceEvent[]): Promise<void> {
    await this.ensureEventLogDirectory();

    const lines = events.map(event => JSON.stringify(event)).join('\n');
    await fs.appendFile(this.eventLogPath, lines + '\n', 'utf-8');
  }

  async writeEvent(event: GovernanceEvent): Promise<void> {
    await this.writeEvents([event]);
  }

  async readEvents(limit?: number): Promise<GovernanceEvent[]> {
    try {
      const content = await fs.readFile(this.eventLogPath, 'utf-8');
      const lines = content.trim().split('\n').filter(line => line.trim());
      
      const events = lines.map(line => JSON.parse(line));
      
      return limit ? events.slice(-limit) : events;
    } catch (error) {
      return [];
    }
  }

  async clearEvents(): Promise<void> {
    try {
      await fs.writeFile(this.eventLogPath, '', 'utf-8');
    } catch (error) {
      // Ignore if file doesn't exist
    }
  }

  private async ensureEventLogDirectory(): Promise<void> {
    const dir = path.dirname(this.eventLogPath);
    await fs.mkdir(dir, { recursive: true });
  }

  async getEventStats(): Promise<{
    total: number;
    byType: Record<string, number>;
    lastEvent?: GovernanceEvent;
  }> {
    const events = await this.readEvents();
    
    const byType: Record<string, number> = {};
    events.forEach(event => {
      byType[event.type] = (byType[event.type] || 0) + 1;
    });

    return {
      total: events.length,
      byType,
      lastEvent: events.length > 0 ? events[events.length - 1] : undefined
    };
  }
}