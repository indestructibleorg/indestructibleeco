/**
 * @ECO-governed
 * @ECO-layer: loader
 * @ECO-semantic: filesystem-loader
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Filesystem Loader
 * Loads artifacts with governance validation
 */

import { promises as fs } from 'fs';
import path from 'path';

export interface LoadResult {
  success: boolean;
  content?: string;
  metadata?: FileMetadata;
  error?: string;
}

export interface FileMetadata {
  path: string;
  size: number;
  modified: Date;
  governance: {
    governed: boolean;
    markers: string[];
    layer?: string;
    semantic?: string;
  };
}

export class FsLoader {
  constructor(private workspace: string = process.cwd()) {}

  async load(filePath: string): Promise<LoadResult> {
    const fullPath = path.resolve(this.workspace, filePath);

    try {
      const content = await fs.readFile(fullPath, 'utf-8');
      const stats = await fs.stat(fullPath);

      const metadata: FileMetadata = {
        path: fullPath,
        size: stats.size,
        modified: stats.mtime,
        governance: this.extractGovernanceInfo(content)
      };

      return {
        success: true,
        content,
        metadata
      };
    } catch (error) {
      return {
        success: false,
        error: `Failed to load file: ${error}`
      };
    }
  }

  async loadDirectory(dirPath: string): Promise<Map<string, LoadResult>> {
    const results = new Map<string, LoadResult>();
    const fullPath = path.resolve(this.workspace, dirPath);

    const scanDir = async (dir: string): Promise<void> => {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const entryPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && 
!['node_modules', '__pycache__', 'dist', 'build'].includes(entry.name)
) {
          await scanDir(entryPath);
        } else if (entry.isFile()) {
          const result = await this.load(entryPath);
          const relativePath = path.relative(this.workspace, entryPath);
          results.set(relativePath, result);
        }
      }
    };

    await scanDir(fullPath);
    return results;
  }

  private extractGovernanceInfo(content: string): FileMetadata['governance'] {
    const governance: FileMetadata['governance'] = {
      governed: false,
      markers: []
    };

    // Check for GL markers
    const governedMatch = content.match(/@ECO-governed/);
    if (governedMatch) {
      governance.governed = true;
      governance.markers.push('@ECO-governed');
    }

    const layerMatch = content.match(/@ECO-layer:\s*(\w+)/);
    if (layerMatch) {
      governance.layer = layerMatch[1];
      governance.markers.push('@ECO-layer');
    }

    const semanticMatch = content.match(/@ECO-semantic:\s*(\w+)/);
    if (semanticMatch) {
      governance.semantic = semanticMatch[1];
      governance.markers.push('@ECO-semantic');
    }

    return governance;
  }
}