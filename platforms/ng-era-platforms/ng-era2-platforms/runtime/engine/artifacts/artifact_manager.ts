/**
 * @ECO-governed
 * @ECO-layer: artifacts
 * @ECO-semantic: artifact-manager
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Artifact Manager
 * Manages governance artifacts with audit trail
 */

import { promises as fs } from 'fs';
import path from 'path';

export interface Artifact {
  id: string;
  name: string;
  type: string;
  content: any;
  metadata: ArtifactMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export interface ArtifactMetadata {
  governance: {
    charter: string;
    version: string;
    layer: string;
    semantic: string;
  };
  audit: {
    createdBy: string;
    modifiedBy: string;
    auditTrail: string[];
  };
  validation: {
    schema: string;
    validated: boolean;
    checksum: string;
  };
}

export class ArtifactManager {
  private artifactsPath: string;

  constructor(private workspace: string = process.cwd()) {
    this.artifactsPath = path.join(workspace, '.governance', 'artifacts');
  }

  async createArtifact(
    name: string,
    type: string,
    content: any,
    metadata: Partial<ArtifactMetadata>
  ): Promise<Artifact> {
    const artifactId = this.generateArtifactId(name);
    const artifactPath = path.join(this.artifactsPath, `${artifactId}.json`);

    const artifact: Artifact = {
      id: artifactId,
      name,
      type,
      content,
      metadata: {
        governance: {
          charter: 'GL Unified Charter',
          version: '1.0.0',
          layer: metadata.governance?.layer || 'unknown',
          semantic: metadata.governance?.semantic || 'unknown'
        },
        audit: {
          createdBy: 'system',
          modifiedBy: 'system',
          auditTrail: [`Created at ${new Date().toISOString()}`]
        },
        validation: {
          schema: metadata.validation?.schema || 'default',
          validated: false,
          checksum: this.calculateChecksum(JSON.stringify(content))
        }
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.ensureArtifactsDirectory();
    await fs.writeFile(artifactPath, JSON.stringify(artifact, null, 2), 'utf-8');

    return artifact;
  }

  async getArtifact(artifactId: string): Promise<Artifact | null> {
    const artifactPath = path.join(this.artifactsPath, `${artifactId}.json`);

    try {
      const content = await fs.readFile(artifactPath, 'utf-8');
      const artifact: Artifact = JSON.parse(content);
      artifact.createdAt = new Date(artifact.createdAt);
      artifact.updatedAt = new Date(artifact.updatedAt);
      return artifact;
    } catch {
      return null;
    }
  }

  async updateArtifact(
    artifactId: string,
    updates: Partial<Artifact>
  ): Promise<Artifact | null> {
    const artifact = await this.getArtifact(artifactId);
    
    if (!artifact) {
      return null;
    }

    const updatedArtifact = {
      ...artifact,
      ...updates,
      metadata: {
        ...artifact.metadata,
        audit: {
          ...artifact.metadata.audit,
          modifiedBy: 'system',
          auditTrail: [
            ...artifact.metadata.audit.auditTrail,
            `Updated at ${new Date().toISOString()}`
          ]
        }
      },
      updatedAt: new Date()
    };

    const artifactPath = path.join(this.artifactsPath, `${artifactId}.json`);
    await fs.writeFile(artifactPath, JSON.stringify(updatedArtifact, null, 2), 'utf-8');

    return updatedArtifact;
  }

  async listArtifacts(filter?: { type?: string }): Promise<Artifact[]> {
    await this.ensureArtifactsDirectory();
    
    const artifacts: Artifact[] = [];
    const entries = await fs.readdir(this.artifactsPath);

    for (const entry of entries) {
      if (entry.endsWith('.json')) {
        const artifactId = entry.replace('.json', '');
        const artifact = await this.getArtifact(artifactId);
        
        if (artifact && (!filter || !filter.type || artifact.type === filter.type)) {
          artifacts.push(artifact);
        }
      }
    }

    return artifacts;
  }

  async deleteArtifact(artifactId: string): Promise<boolean> {
    const artifactPath = path.join(this.artifactsPath, `${artifactId}.json`);

    try {
      await fs.unlink(artifactPath);
      return true;
    } catch {
      return false;
    }
  }

  private generateArtifactId(name: string): string {
    const timestamp = Date.now();
    const hash = Buffer.from(name).toString('base64').slice(0, 8);
    return `ECO-${hash}-${timestamp}`;
  }

  private calculateChecksum(content: string): string {
    // Simple checksum calculation
    let checksum = 0;
    for (let i = 0; i < content.length; i++) {
      checksum = ((checksum << 5) - checksum) + content.charCodeAt(i);
      checksum = checksum & checksum;
    }
    return checksum.toString(16);
  }

  private async ensureArtifactsDirectory(): Promise<void> {
    await fs.mkdir(this.artifactsPath, { recursive: true });
  }
}