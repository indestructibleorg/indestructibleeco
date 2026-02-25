/**
 * @ECO-governed
 * @ECO-layer: governance
 * @ECO-semantic: anchor-resolution
 * @ECO-audit-trail: GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - Semantic Anchor Resolver
 * Resolves and validates GL semantic anchors
 */

import { promises as fs } from 'fs';
import path from 'path';

export interface SemanticAnchor {
  governance: {
    charter: string;
    version: string;
    activation: string;
  };
  semantic: {
    anchor: {
      id: string;
      namespace: string;
      description: string;
    };
    hierarchy: {
      levels: string[];
    };
    metadata: {
      required: string[];
    };
  };
  enforcement: {
    strict: boolean;
    continue_on_error: boolean;
    validation_required: boolean;
    audit_trail_required: boolean;
  };
}

export class AnchorResolver {
  private anchorPath: string;
  private anchor: SemanticAnchor | null = null;

  constructor(private workspace: string = process.cwd()) {
    this.anchorPath = path.join(workspace, 'governance', 'GL_SEMANTIC_ANCHOR.json');
  }

  async loadAnchor(): Promise<boolean> {
    try {
      const content = await fs.readFile(this.anchorPath, 'utf-8');
      this.anchor = JSON.parse(content);
      return this.validateAnchor();
    } catch (error) {
      return false;
    }
  }

  private validateAnchor(): boolean {
    if (!this.anchor) return false;

    // Validate governance section
    if (!this.anchor.governance?.charter || !this.anchor.governance?.version) {
      return false;
    }

    // Validate semantic section
    if (!this.anchor.semantic?.anchor?.id || !this.anchor.semantic?.anchor?.namespace) {
      return false;
    }

    // Validate enforcement section
    if (typeof this.anchor.enforcement?.strict !== 'boolean') {
      return false;
    }

    return true;
  }

  getAnchor(): SemanticAnchor | null {
    return this.anchor;
  }

  getAnchorId(): string | null {
    return this.anchor?.semantic.anchor.id || null;
  }

  getNamespace(): string | null {
    return this.anchor?.semantic.anchor.namespace || null;
  }

  isStrictMode(): boolean {
    return this.anchor?.enforcement.strict ?? false;
  }

  isContinueOnError(): boolean {
    return this.anchor?.enforcement.continue_on_error ?? false;
  }

  getRequiredMetadata(): string[] {
    return this.anchor?.semantic.metadata.required || [];
  }

  async resolveHierarchy(level: string): Promise<string[]> {
    if (!this.anchor) return [];

    const hierarchy = this.anchor.semantic.hierarchy.levels;
    const index = hierarchy.indexOf(level);
    
    if (index === -1) return [];
    
    return hierarchy.slice(0, index + 1);
  }
}