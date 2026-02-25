/**
 * @ECO-governed
 * @ECO-layer: artifacts
 * @ECO-semantic: manifest-generator
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Manifest Generator
 * Generates governance manifests with semantic metadata
 */

import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

export interface Manifest {
  id: string;
  version: string;
  timestamp: string;
  governance: {
    charter: string;
    semanticAnchor: string;
    enforcement: 'strict' | 'lenient';
  };
  artifacts: ManifestArtifact[];
  metadata: {
    totalArtifacts: number;
    governedArtifacts: number;
    complianceRate: number;
    checksum: string;
  };
}

export interface ManifestArtifact {
  path: string;
  type: string;
  governed: boolean;
  layer?: string;
  semantic?: string;
  checksum: string;
}

export class ManifestGenerator {
  private manifestPath: string;

  constructor(private workspace: string = process.cwd()) {
    this.manifestPath = path.join(workspace, '.governance', 'manifest.json');
  }

  async generateManifest(): Promise<Manifest> {
    const artifacts = await this.scanArtifacts();
    
    const governedArtifacts = artifacts.filter(a => a.governed);
    const complianceRate = artifacts.length > 0 
      ? (governedArtifacts.length / artifacts.length) * 100 
      : 0;

    const manifest: Manifest = {
      id: this.generateManifestId(),
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      governance: {
        charter: 'GL Unified Charter',
        semanticAnchor: 'ECO-ROOT-SEMANTIC-ANCHOR',
        enforcement: 'strict'
      },
      artifacts,
      metadata: {
        totalArtifacts: artifacts.length,
        governedArtifacts: governedArtifacts.length,
        complianceRate,
        checksum: this.calculateChecksum(JSON.stringify(artifacts))
      }
    };

    await this.saveManifest(manifest);
    return manifest;
  }

  async getManifest(): Promise<Manifest | null> {
    try {
      const content = await fs.readFile(this.manifestPath, 'utf-8');
      const manifest: Manifest = JSON.parse(content);
      manifest.timestamp = new Date(manifest.timestamp).toISOString();
      return manifest;
    } catch {
      return null;
    }
  }

  async validateManifest(manifest: Manifest): Promise<boolean> {
    // Verify manifest structure
    if (!manifest.id || !manifest.version || !manifest.governance) {
      return false;
    }

    // Verify checksum
    const calculatedChecksum = this.calculateChecksum(JSON.stringify(manifest.artifacts));
    if (calculatedChecksum !== manifest.metadata.checksum) {
      return false;
    }

    return true;
  }

  private async scanArtifacts(): Promise<ManifestArtifact[]> {
    const artifacts: ManifestArtifact[] = [];
    const engineDir = path.join(this.workspace, 'engine');

    const scanDir = async (dir: string): Promise<void> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        const relativePath = path.relative(this.workspace, fullPath);
        
        if (entry.isDirectory() && 
!['node_modules', '__pycache__', 'dist', 'build'].includes(entry.name)
) {
          await scanDir(fullPath);
        } else if (entry.isFile() && /\.(ts|tsx|js|json|yaml|yml)$/.test(entry.name)) {
          const content = await fs.readFile(fullPath, 'utf-8');
          const artifact: ManifestArtifact = {
            path: relativePath,
            type: path.extname(entry.name),
            governed: content.includes('@ECO-governed'),
            layer: this.extractMarker(content, '@ECO-layer:'),
            semantic: this.extractMarker(content, '@ECO-semantic:'),
            checksum: this.calculateChecksum(content)
          };
          artifacts.push(artifact);
        }
      }
    };

    await scanDir(engineDir);
    return artifacts;
  }

  private extractMarker(content: string, marker: string): string | undefined {
    const match = content.match(new RegExp(`${marker}(\\w+)`));
    return match ? match[1] : undefined;
  }

  private generateManifestId(): string {
    return `ECO-MANIFEST-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
  }

  private calculateChecksum(content: string): string {
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  private async saveManifest(manifest: Manifest): Promise<void> {
    const dir = path.dirname(this.manifestPath);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(this.manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
  }
}