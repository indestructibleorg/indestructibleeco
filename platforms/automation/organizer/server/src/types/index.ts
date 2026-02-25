/**
 * @ECO-governed
 * @ECO-layer: server
 * @ECO-semantic: type-definitions
 * @ECO-audit-trail: ../.governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated - File Organizer Type Definitions
 */

export interface File {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  createdAt: Date;
  modifiedAt: Date;
  governance?: {
    governed: boolean;
    layer?: string;
    semantic?: string;
  };
}

export interface Rule {
  id: string;
  name: string;
  description: string;
  pattern: string;
  action: 'move' | 'copy' | 'delete';
  destination: string;
  enabled: boolean;
  createdAt: Date;
  governance?: {
    governed: boolean;
    layer?: string;
    semantic?: string;
  };
}

export interface Task {
  id: string;
  type: 'classify' | 'organize' | 'validate';
  status: 'pending' | 'running' | 'completed' | 'failed';
  files: string[];
  result?: any;
  createdAt: Date;
  completedAt?: Date;
  governance?: {
    governed: boolean;
    layer?: string;
    semantic?: string;
  };
}