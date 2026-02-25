/**
 * @ECO-governed
 * @ECO-layer: artifacts
 * @ECO-semantic: evidence-chain
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Evidence Chain
 * Maintains immutable evidence chain for audit trail
 */

import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

export interface Evidence {
  id: string;
  timestamp: string;
  type: string;
  source: string;
  data: any;
  hash: string;
  previousHash: string;
}

export class EvidenceChain {
  private chainPath: string;
  private chain: Evidence[] = [];

  constructor(private workspace: string = process.cwd()) {
    this.chainPath = path.join(workspace, '.governance', 'evidence-chain.jsonl');
  }

  async initialize(): Promise<void> {
    try {
      const content = await fs.readFile(this.chainPath, 'utf-8');
      const lines = content.trim().split('\n').filter(line => line.trim());
      
      this.chain = lines.map(line => {
        const evidence: Evidence = JSON.parse(line);
        evidence.timestamp = new Date(evidence.timestamp).toISOString();
        return evidence;
      });
    } catch {
      this.chain = [];
    }
  }

  async addEvidence(
    type: string,
    source: string,
    data: any
  ): Promise<Evidence> {
    await this.initialize();

    const previousEvidence = this.chain.length > 0 
      ? this.chain[this.chain.length - 1] 
      : null;

    const evidence: Evidence = {
      id: this.generateEvidenceId(),
      timestamp: new Date().toISOString(),
      type,
      source,
      data,
      hash: '',
      previousHash: previousEvidence ? previousEvidence.hash : '0'
    };

    evidence.hash = this.calculateHash(evidence);
    this.chain.push(evidence);

    await this.saveChain();
    return evidence;
  }

  async verifyChain(): Promise<{ valid: boolean; brokenAt?: string }> {
    await this.initialize();

    for (let i = 0; i < this.chain.length; i++) {
      const evidence = this.chain[i];
      const calculatedHash = this.calculateHash({
        ...evidence,
        hash: ''
      });

      if (calculatedHash !== evidence.hash) {
        return {
          valid: false,
          brokenAt: evidence.id
        };
      }

      if (i > 0) {
        const previousEvidence = this.chain[i - 1];
        if (evidence.previousHash !== previousEvidence.hash) {
          return {
            valid: false,
            brokenAt: evidence.id
          };
        }
      }
    }

    return { valid: true };
  }

  async getEvidence(id: string): Promise<Evidence | null> {
    await this.initialize();
    return this.chain.find(e => e.id === id) || null;
  }

  async getChainHistory(limit?: number): Promise<Evidence[]> {
    await this.initialize();
    return limit ? this.chain.slice(-limit) : this.chain;
  }

  private async saveChain(): Promise<void> {
    const dir = path.dirname(this.chainPath);
    await fs.mkdir(dir, { recursive: true });

    const lines = this.chain.map(e => JSON.stringify(e)).join('\n');
    await fs.writeFile(this.chainPath, lines + '\n', 'utf-8');
  }

  private generateEvidenceId(): string {
    return `EVID-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
  }

  private calculateHash(evidence: Evidence): string {
    const data = JSON.stringify({
      id: evidence.id,
      timestamp: evidence.timestamp,
      type: evidence.type,
      source: evidence.source,
      data: evidence.data,
      previousHash: evidence.previousHash
    });

    return crypto.createHash('sha256').update(data).digest('hex');
  }
}