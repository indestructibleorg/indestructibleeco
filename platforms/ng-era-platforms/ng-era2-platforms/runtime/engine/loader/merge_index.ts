/**
 * @ECO-governed
 * @ECO-layer: loader
 * @ECO-semantic: merge-index
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Merge Index
 * Merges loaded artifacts with governance validation
 */

import { FsLoader, LoadResult } from './fs_loader';

export interface MergeResult {
  success: boolean;
  artifacts: Map<string, any>;
  governance: {
    totalFiles: number;
    governedFiles: number;
    ungovernedFiles: number;
  };
  errors: string[];
}

export class MergeIndex {
  private loader: FsLoader;

  constructor(private workspace: string = process.cwd()) {
    this.loader = new FsLoader(workspace);
  }

  async merge(paths: string[]): Promise<MergeResult> {
    const result: MergeResult = {
      success: true,
      artifacts: new Map(),
      governance: {
        totalFiles: 0,
        governedFiles: 0,
        ungovernedFiles: 0
      },
      errors: []
    };

    for (const loadPath of paths) {
      try {
        const loadResults = await this.loader.loadDirectory(loadPath);
        
        for (const [relativePath, loadResult] of loadResults.entries()) {
          if (loadResult.success) {
            result.artifacts.set(relativePath, {
              content: loadResult.content,
              metadata: loadResult.metadata
            });

            result.governance.totalFiles++;
            
            if (loadResult.metadata?.governance.governed) {
              result.governance.governedFiles++;
            } else {
              result.governance.ungovernedFiles++;
            }
          } else {
            result.errors.push(`${relativePath}: ${loadResult.error}`);
          }
        }
      } catch (error) {
        result.errors.push(`Failed to load ${loadPath}: ${error}`);
        result.success = false;
      }
    }

    return result;
  }

  async mergeAll(): Promise<MergeResult> {
    return this.merge(['.']);
  }

  async getGovernanceCompliance(): Promise<number> {
    const result = await this.mergeAll();
    
    if (result.governance.totalFiles === 0) {
      return 0;
    }

    return (result.governance.governedFiles / result.governance.totalFiles) * 100;
  }
}