// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: migration-planner
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as fs from 'fs';
import * as path from 'path';
import { MigrationPlan, MigrationStep, AnalysisResult, Recommendation } from '../types';

export class MigrationPlanner {
  private migrationPatterns: { [key: string]: any } = {
    'react-class-to-hooks': {
      sourceFramework: 'React Class Components',
      targetFramework: 'React Hooks',
      patterns: [
        { regex: /class\s+\w+\s+extends\s+(React\.)?Component/g, file: true },
        { regex: /componentDidMount/g, file: true },
        { regex: /componentDidUpdate/g, file: true },
        { regex: /componentWillUnmount/g, file: true },
        { regex: /setState/g, file: true },
        { regex: /this\.state\./g, file: true },
        { regex: /this\.props\./g, file: true }
      ]
    },
    'javascript-to-typescript': {
      sourceFramework: 'JavaScript',
      targetFramework: 'TypeScript',
      patterns: [
        { regex: /\.js$/g, file: true },
        { regex: /function\s+\w+\s*\([^)]*\)/g, file: true },
        { regex: /const\s+\w+\s*=\s*\([^)]*\)\s*=>/g, file: true },
        { regex: /\/\/\s*@ts-ignore/g, file: true },
        { regex: /any\s*\[/g, file: true }
      ]
    },
    'vue2-to-vue3': {
      sourceFramework: 'Vue 2',
      targetFramework: 'Vue 3',
      patterns: [
        { regex: /new Vue\(/g, file: true },
        { regex: /Vue\.component/g, file: true },
        { regex: /Vue\.use/g, file: true },
        { regex: /v-model/g, file: true },
        { regex: /\$refs/g, file: true }
      ]
    },
    'angularjs-to-angular': {
      sourceFramework: 'AngularJS',
      targetFramework: 'Angular',
      patterns: [
        { regex: /angular\.module/g, file: true },
        { regex: /\$scope/g, file: true },
        { regex: /\$http/g, file: true },
        { regex: /ng-controller/g, file: true },
        { regex: /ng-repeat/g, file: true }
      ]
    }
  };

  planMigration(repoPath: string, migrationType: string): AnalysisResult {
    const migration = this.analyzeMigration(repoPath, migrationType);
    const effort = this.estimateEffort(migration);
    const breakingChanges = this.identifyBreakingChanges(migrationType);

    return {
      type: 'migration',
      summary: `Migration plan for ${migration.sourceFramework} to ${migration.targetFramework}. ${migration.filesToChange.length} files to change. Estimated effort: ${effort}`,
      data: {
        migration,
        effort,
        breakingChanges
      },
      insights: [
        `${migration.filesToChange.length} files require migration`,
        `Estimated ${effort} effort level`,
        `${breakingChanges.length} breaking changes identified`,
        'Step-by-step migration plan generated'
      ],
      recommendations: this.generateRecommendations(migration, effort),
      generatedAt: new Date()
    };
  }

  private analyzeMigration(repoPath: string, migrationType: string): MigrationPlan {
    const pattern = this.migrationPatterns[migrationType];
    
    if (!pattern) {
      throw new Error(`Unknown migration type: ${migrationType}`);
    }

    const filesToChange = this.findFilesToChange(repoPath, pattern.patterns);
    const breakingChanges = this.identifyBreakingChanges(migrationType);
    const steps = this.generateMigrationSteps(migrationType, filesToChange);

    return {
      sourceFramework: pattern.sourceFramework,
      targetFramework: pattern.targetFramework,
      filesToChange,
      estimatedEffort: this.determineEffort(filesToChange.length),
      breakingChanges,
      steps
    };
  }

  private findFilesToChange(repoPath: string, patterns: any[]): string[] {
    const files: string[] = [];

    this.walkDirectory(repoPath, (filePath) => {
      const ext = path.extname(filePath).toLowerCase();
      
      // Only check relevant file types
      if (['.js', '.jsx', '.ts', '.tsx', '.vue', '.html'].includes(ext)) {
        const content = fs.readFileSync(filePath, 'utf-8');
        
        for (const pattern of patterns) {
          if (pattern.file) {
            const regex = new RegExp(pattern.regex);
            if (regex.test(content)) {
              files.push(path.relative(process.cwd(), filePath));
              break;
            }
          }
        }
      }
    });

    return files;
  }

  private identifyBreakingChanges(migrationType: string): string[] {
    const breakingChanges: { [key: string]: string[] } = {
      'react-class-to-hooks': [
        'Lifecycle methods must be converted to useEffect',
        'State must be converted to useState',
        'Context must be converted to useContext',
        'Refs must be converted to useRef',
        'Event handlers must use useCallback',
        'Computed values must use useMemo',
        'Component instance properties are no longer available'
      ],
      'javascript-to-typescript': [
        'Type annotations required for all functions and variables',
        'Interface or type definitions needed for complex objects',
        'Implicit any types must be resolved',
        'Third-party libraries may need type definitions (@types/*)',
        'Config files require tsconfig.json adjustments',
        'Build tools must support TypeScript compilation'
      ],
      'vue2-to-vue3': [
        'Options API to Composition API migration',
        'v-model syntax changes for custom components',
        'Event modifiers updated',
        'Global API changes (Vue.createApp)',
        'Removed filters',
        'Portal API changes',
        'Transition API changes'
      ],
      'angularjs-to-angular': [
        'Complete rewrite required (not a direct migration)',
        '$scope replaced by component properties',
        '$http replaced by HttpClient',
        'Directives replaced by @Directive decorator',
        'Services now use @Injectable decorator',
        'Template syntax completely different',
        'Routing system completely different'
      ]
    };

    return breakingChanges[migrationType] || [];
  }

  private generateMigrationSteps(migrationType: string, files: string[]): MigrationStep[] {
    const steps: MigrationStep[] = [];

    switch (migrationType) {
      case 'react-class-to-hooks':
        steps.push({
          step: 1,
          description: 'Install required dependencies and configure project',
          files: ['package.json', 'tsconfig.json'],
          codeExample: 'npm install @types/react @types/react-dom',
          estimatedTime: '30 minutes'
        });
        steps.push({
          step: 2,
          description: 'Convert class components to functional components',
          files,
          codeExample: `// Before\nclass MyComponent extends React.Component {\n  state = { count: 0 };\n  render() { return <div>{this.state.count}</div>; }\n}\n\n// After\nfunction MyComponent() {\n  const [count, setCount] = useState(0);\n  return <div>{count}</div>;\n}`,
          estimatedTime: `${files.length * 15} minutes`
        });
        steps.push({
          step: 3,
          description: 'Convert lifecycle methods to useEffect hooks',
          files,
          codeExample: `useEffect(() => {\n  // componentDidMount logic\n  return () => {\n    // componentWillUnmount logic\n  };\n}, [dependencies]);`,
          estimatedTime: `${files.length * 10} minutes`
        });
        steps.push({
          step: 4,
          description: 'Replace this.state with useState',
          files,
          codeExample: 'const [state, setState] = useState(initialState);',
          estimatedTime: `${files.length * 5} minutes`
        });
        steps.push({
          step: 5,
          description: 'Replace this.props with function parameters',
          files,
          codeExample: 'function MyComponent({ prop1, prop2 }) { ... }',
          estimatedTime: `${files.length * 5} minutes`
        });
        break;

      case 'javascript-to-typescript':
        steps.push({
          step: 1,
          description: 'Install TypeScript and configure project',
          files: ['package.json', 'tsconfig.json'],
          codeExample: 'npm install -D typescript @types/node @types/react',
          estimatedTime: '30 minutes'
        });
        steps.push({
          step: 2,
          description: 'Rename .js files to .ts',
          files,
          codeExample: 'mv file.js file.ts',
          estimatedTime: `${files.length * 1} minutes`
        });
        steps.push({
          step: 3,
          description: 'Add type annotations to functions',
          files,
          codeExample: 'function greet(name: string): string { return `Hello, ${name}`; }',
          estimatedTime: `${files.length * 20} minutes`
        });
        steps.push({
          step: 4,
          description: 'Define interfaces for complex objects',
          files,
          codeExample: 'interface User { id: number; name: string; }',
          estimatedTime: `${files.length * 15} minutes`
        });
        steps.push({
          step: 5,
          description: 'Fix TypeScript compilation errors',
          files,
          codeExample: '// Fix any type errors reported by tsc',
          estimatedTime: `${files.length * 10} minutes`
        });
        break;

      default:
        steps.push({
          step: 1,
          description: 'Analyze codebase and create migration strategy',
          files,
          estimatedTime: '1-2 days'
        });
        steps.push({
          step: 2,
          description: 'Create new project structure for target framework',
          files: ['package.json', 'configuration files'],
          estimatedTime: '2-4 hours'
        });
        steps.push({
          step: 3,
          description: 'Migrate components and features incrementally',
          files,
          estimatedTime: '2-4 weeks'
        });
        steps.push({
          step: 4,
          description: 'Test and validate migrated code',
          files,
          estimatedTime: '1-2 weeks'
        });
    }

    return steps;
  }

  private determineEffort(fileCount: number): 'low' | 'medium' | 'high' | 'very-high' {
    if (fileCount < 10) return 'low';
    if (fileCount < 50) return 'medium';
    if (fileCount < 100) return 'high';
    return 'very-high';
  }

  private estimateEffort(migration: MigrationPlan): string {
    const effortMap: { [key: string]: string } = {
      'low': '1-2 days',
      'medium': '1-2 weeks',
      'high': '2-4 weeks',
      'very-high': '1-3 months'
    };

    return effortMap[migration.estimatedEffort] || 'unknown';
  }

  private generateRecommendations(migration: MigrationPlan, effort: string): Recommendation[] {
    const recommendations: Recommendation[] = [];

    recommendations.push({
      category: 'planning',
      priority: 'high',
      description: 'Create detailed migration roadmap with milestones',
      actionable: true,
      estimatedEffort: '1-2 days'
    });

    recommendations.push({
      category: 'execution',
      priority: 'high',
      description: 'Migrate incrementally with feature flags',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    recommendations.push({
      category: 'testing',
      priority: 'critical',
      description: 'Implement comprehensive testing before and after migration',
      actionable: true,
      estimatedEffort: '1-2 weeks'
    });

    recommendations.push({
      category: 'documentation',
      priority: 'medium',
      description: 'Document migration process and lessons learned',
      actionable: true,
      estimatedEffort: '2-4 hours'
    });

    if (migration.estimatedEffort === 'high' || migration.estimatedEffort === 'very-high') {
      recommendations.push({
        category: 'resources',
        priority: 'medium',
        description: 'Allocate dedicated team for migration',
        actionable: true,
        estimatedEffort: '1 week'
      });
    }

    return recommendations;
  }

  private walkDirectory(dir: string, callback: (filePath: string) => void): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!['node_modules', '.git', 'dist', 'build', 'target', 'bin'].includes(entry.name)) {
          this.walkDirectory(fullPath, callback);
        }
      } else if (entry.isFile()) {
        callback(fullPath);
      }
    }
  }
}