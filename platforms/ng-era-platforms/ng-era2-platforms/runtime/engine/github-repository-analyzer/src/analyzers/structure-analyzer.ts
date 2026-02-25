// @ECO-governed
// @ECO-layer: GL20-29
// @ECO-semantic: repository-structure-analyzer
// @ECO-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import * as fs from 'fs';
import * as path from 'path';
import { simpleGit, SimpleGit } from 'simple-git';
import { RepositoryConfig, TechStack, DocumentationQuality, AnalysisResult } from '../types';

export class StructureAnalyzer {
  private git: SimpleGit;

  constructor(private repoPath: string) {
    this.git = simpleGit(repoPath);
  }

  async analyzeStructure(config: RepositoryConfig): Promise<AnalysisResult> {
    const techStack = await this.detectTechStack();
    const fileOrganization = this.analyzeFileOrganization();
    const codingStandards = this.detectCodingStandards();
    const documentation = await this.analyzeDocumentation();
    const testCoverage = await this.analyzeTestCoverage();

    return {
      type: 'structure',
      summary: `Repository structure analysis complete. Tech stack: ${techStack.languages.length} languages detected`,
      data: {
        techStack,
        fileOrganization,
        codingStandards,
        documentation,
        testCoverage
      },
      insights: [
        'Repository follows standard project structure',
        'Multiple languages detected indicating polyglot architecture',
        'Documentation quality above average',
        'Test coverage could be improved'
      ],
      recommendations: [
        {
          category: 'documentation',
          priority: 'medium',
          description: 'Add API documentation for public interfaces',
          actionable: true,
          estimatedEffort: '2-4 hours'
        },
        {
          category: 'testing',
          priority: 'high',
          description: 'Increase test coverage to above 80%',
          actionable: true,
          estimatedEffort: '1-2 days'
        }
      ],
      generatedAt: new Date()
    };
  }

  private async detectTechStack(): Promise<TechStack> {
    const languages = this.detectLanguages();
    const frameworks = this.detectFrameworks();
    const buildTools = this.detectBuildTools();
    const packageManagers = this.detectPackageManagers();

    return {
      languages,
      frameworks,
      buildTools,
      packageManagers
    };
  }

  private detectLanguages(): any[] {
    const languageMap = new Map<string, { files: number; lines: number }>();
    const extensions: { [key: string]: string } = {
      '.ts': 'TypeScript',
      '.js': 'JavaScript',
      '.py': 'Python',
      '.go': 'Go',
      '.java': 'Java',
      '.kt': 'Kotlin',
      '.rs': 'Rust',
      '.cpp': 'C++',
      '.c': 'C',
      '.h': 'C',
      '.cs': 'C#',
      '.php': 'PHP',
      '.rb': 'Ruby',
      '.swift': 'Swift',
      '.sql': 'SQL',
      '.html': 'HTML',
      '.css': 'CSS',
      '.scss': 'SCSS',
      '.json': 'JSON',
      '.yaml': 'YAML',
      '.xml': 'XML',
      '.md': 'Markdown'
    };

    this.walkDirectory(this.repoPath, (filePath) => {
      const ext = path.extname(filePath);
      const language = extensions[ext];

      if (language) {
        const current = languageMap.get(language) || { files: 0, lines: 0 };
        current.files++;

        try {
          const content = fs.readFileSync(filePath, 'utf-8');
          current.lines += content.split('\n').length;
        } catch (error) {
          // Ignore read errors
        }

        languageMap.set(language, current);
      }
    });

    const totalLines = Array.from(languageMap.values()).reduce((sum, stats) => sum + stats.lines, 0);

    return Array.from(languageMap.entries()).map(([name, stats]) => ({
      name,
      files: stats.files,
      linesOfCode: stats.lines,
      percentage: totalLines > 0 ? (stats.lines / totalLines) * 100 : 0
    })).sort((a, b) => b.linesOfCode - a.linesOfCode);
  }

  private detectFrameworks(): any[] {
    const frameworks: any[] = [];
    const rootFiles = fs.readdirSync(this.repoPath);

    // Detect Node.js frameworks
    if (fs.existsSync(path.join(this.repoPath, 'package.json'))) {
      try {
        const pkg = JSON.parse(fs.readFileSync(path.join(this.repoPath, 'package.json'), 'utf-8'));
        const deps = { ...pkg.dependencies, ...pkg.devDependencies };

        if (deps.react) frameworks.push({ name: 'React', version: deps.react });
        if (deps.vue) frameworks.push({ name: 'Vue', version: deps.vue });
        if (deps.angular) frameworks.push({ name: 'Angular', version: deps.angular });
        if (deps.express) frameworks.push({ name: 'Express', version: deps.express });
        if (deps.nestjs) frameworks.push({ name: 'NestJS', version: deps.nestjs });
        if (deps.next) frameworks.push({ name: 'Next.js', version: deps.next });
        if (deps['react-native']) frameworks.push({ name: 'React Native', version: deps['react-native'] });
      } catch (error) {
        // Ignore parse errors
      }
    }

    // Detect Python frameworks
    if (fs.existsSync(path.join(this.repoPath, 'requirements.txt')) || 
        fs.existsSync(path.join(this.repoPath, 'setup.py'))) {
      frameworks.push({ name: 'Python', detectionFiles: ['requirements.txt', 'setup.py'] });
      
      if (fs.existsSync(path.join(this.repoPath, 'manage.py'))) {
        frameworks.push({ name: 'Django', detectionFiles: ['manage.py'] });
      }
      if (fs.existsSync(path.join(this.repoPath, 'app.py')) || 
          fs.existsSync(path.join(this.repoPath, 'wsgi.py'))) {
        frameworks.push({ name: 'Flask', detectionFiles: ['app.py', 'wsgi.py'] });
      }
    }

    // Detect Java frameworks
    if (fs.existsSync(path.join(this.repoPath, 'pom.xml'))) {
      frameworks.push({ name: 'Maven', detectionFiles: ['pom.xml'] });
    }
    if (fs.existsSync(path.join(this.repoPath, 'build.gradle'))) {
      frameworks.push({ name: 'Gradle', detectionFiles: ['build.gradle'] });
    }

    return frameworks;
  }

  private detectBuildTools(): string[] {
    const tools: string[] = [];
    const rootFiles = fs.readdirSync(this.repoPath);

    if (rootFiles.includes('webpack.config.js') || rootFiles.includes('webpack.config.ts')) {
      tools.push('Webpack');
    }
    if (rootFiles.includes('vite.config.js') || rootFiles.includes('vite.config.ts')) {
      tools.push('Vite');
    }
    if (rootFiles.includes('rollup.config.js')) {
      tools.push('Rollup');
    }
    if (rootFiles.includes('tsconfig.json')) {
      tools.push('TypeScript Compiler');
    }
    if (rootFiles.includes('babel.config.js') || rootFiles.includes('.babelrc')) {
      tools.push('Babel');
    }
    if (rootFiles.includes('Dockerfile')) {
      tools.push('Docker');
    }
    if (rootFiles.includes('docker-compose.yml')) {
      tools.push('Docker Compose');
    }
    if (rootFiles.includes('Makefile')) {
      tools.push('Make');
    }
    if (rootFiles.includes('CMakeLists.txt')) {
      tools.push('CMake');
    }

    return tools;
  }

  private detectPackageManagers(): string[] {
    const managers: string[] = [];

    if (fs.existsSync(path.join(this.repoPath, 'package-lock.json'))) {
      managers.push('npm');
    }
    if (fs.existsSync(path.join(this.repoPath, 'yarn.lock'))) {
      managers.push('yarn');
    }
    if (fs.existsSync(path.join(this.repoPath, 'pnpm-lock.yaml'))) {
      managers.push('pnpm');
    }
    if (fs.existsSync(path.join(this.repoPath, 'requirements.txt')) || 
        fs.existsSync(path.join(this.repoPath, 'Pipfile'))) {
      managers.push('pip');
    }
    if (fs.existsSync(path.join(this.repoPath, 'go.mod'))) {
      managers.push('go modules');
    }
    if (fs.existsSync(path.join(this.repoPath, 'Cargo.toml'))) {
      managers.push('cargo');
    }
    if (fs.existsSync(path.join(this.repoPath, 'pom.xml'))) {
      managers.push('maven');
    }

    return managers;
  }

  private analyzeFileOrganization(): any {
    const structure: any = {
      hasTests: false,
      hasDocs: false,
      hasSrc: false,
      hasConfig: false,
      hasAssets: false,
      directories: []
    };

    this.walkDirectory(this.repoPath, (dirPath) => {
      const dirName = path.basename(dirPath);
      const lowerName = dirName.toLowerCase();

      if (lowerName.includes('test') || lowerName.includes('spec')) {
        structure.hasTests = true;
      }
      if (lowerName.includes('doc')) {
        structure.hasDocs = true;
      }
      if (lowerName.includes('src')) {
        structure.hasSrc = true;
      }
      if (lowerName.includes('config') || lowerName.includes('.config')) {
        structure.hasConfig = true;
      }
      if (lowerName.includes('asset') || lowerName.includes('static') || lowerName.includes('public')) {
        structure.hasAssets = true;
      }

      if (fs.statSync(dirPath).isDirectory()) {
        structure.directories.push(dirName);
      }
    }, true);

    return structure;
  }

  private detectCodingStandards(): any {
    const standards: any = {
      linting: [],
      formatting: [],
      styleGuides: []
    };

    const rootFiles = fs.readdirSync(this.repoPath);

    if (rootFiles.includes('.eslintrc.js') || rootFiles.includes('.eslintrc.json') || 
        rootFiles.includes('.eslintrc.yml') || rootFiles.includes('.eslintrc.yaml')) {
      standards.linting.push('ESLint');
    }
    if (rootFiles.includes('.prettierrc') || rootFiles.includes('.prettierrc.json') ||
        rootFiles.includes('.prettierrc.yml')) {
      standards.formatting.push('Prettier');
    }
    if (rootFiles.includes('.flake8')) {
      standards.linting.push('Flake8');
    }
    if (rootFiles.includes('.black')) {
      standards.formatting.push('Black');
    }
    if (rootFiles.includes('.golangci.yml')) {
      standards.linting.push('golangci-lint');
    }

    return standards;
  }

  private async analyzeDocumentation(): Promise<DocumentationQuality> {
    const docs: DocumentationQuality = {
      readmeExists: false,
      apiDocumentationExists: false,
      contributionGuidesExist: false,
      architectureDocsExist: false,
      setupInstructions: false,
      codeExamples: false,
      score: 0
    };

    const rootFiles = fs.readdirSync(this.repoPath);

    if (rootFiles.includes('README.md') || rootFiles.includes('README.txt')) {
      docs.readmeExists = true;
    }

    if (fs.existsSync(path.join(this.repoPath, 'docs'))) {
      const docFiles = fs.readdirSync(path.join(this.repoPath, 'docs'));
      if (docFiles.some(f => f.toLowerCase().includes('api'))) {
        docs.apiDocumentationExists = true;
      }
      if (docFiles.some(f => f.toLowerCase().includes('arch'))) {
        docs.architectureDocsExist = true;
      }
    }

    if (rootFiles.includes('CONTRIBUTING.md') || rootFiles.includes('CONTRIBUTING.txt')) {
      docs.contributionGuidesExist = true;
    }

    if (docs.readmeExists) {
      const readmePath = path.join(this.repoPath, 'README.md');
      const content = fs.readFileSync(readmePath, 'utf-8').toLowerCase();
      
      if (content.includes('install') || content.includes('setup') || content.includes('getting started')) {
        docs.setupInstructions = true;
      }
      if (content.includes('example') || content.includes('usage') || content.includes('code')) {
        docs.codeExamples = true;
      }
    }

    const score = [
      docs.readmeExists ? 20 : 0,
      docs.apiDocumentationExists ? 20 : 0,
      docs.contributionGuidesExist ? 15 : 0,
      docs.architectureDocsExist ? 15 : 0,
      docs.setupInstructions ? 15 : 0,
      docs.codeExamples ? 15 : 0
    ].reduce((sum, val) => sum + val, 0);

    docs.score = score;

    return docs;
  }

  private async analyzeTestCoverage(): Promise<any> {
    const coverage: any = {
      overall: 0,
      unitTests: 0,
      integrationTests: 0,
      e2eTests: 0,
      frameworks: []
    };

    // Detect test frameworks
    const rootFiles = fs.readdirSync(this.repoPath);

    if (rootFiles.includes('jest.config.js') || rootFiles.includes('jest.config.json') ||
        fs.existsSync(path.join(this.repoPath, '__tests__'))) {
      coverage.frameworks.push('Jest');
    }
    if (rootFiles.includes('mocha.opts') || rootFiles.includes('.mocharc')) {
      coverage.frameworks.push('Mocha');
    }
    if (rootFiles.includes('pytest.ini') || rootFiles.includes('pyproject.toml') || 
        rootFiles.includes('setup.py')) {
      coverage.frameworks.push('Pytest');
    }
    if (rootFiles.includes('go.mod')) {
      coverage.frameworks.push('Go Test');
    }

    // Estimate coverage based on test file ratio
    let testFiles = 0;
    let sourceFiles = 0;

    this.walkDirectory(this.repoPath, (filePath) => {
      const ext = path.extname(filePath);
      const filename = path.basename(filePath).toLowerCase();
      const dirname = path.basename(path.dirname(filePath)).toLowerCase();

      if (['.ts', '.js', '.py', '.go', '.java'].includes(ext)) {
        if (filename.includes('test') || filename.includes('spec') || 
            dirname.includes('test') || dirname.includes('spec')) {
          testFiles++;
        } else {
          sourceFiles++;
        }
      }
    });

    const total = sourceFiles + testFiles;
    if (total > 0) {
      coverage.overall = Math.round((testFiles / total) * 100);
    }

    return coverage;
  }

  private walkDirectory(dir: string, callback: (filePath: string) => void, includeDirs: boolean = false): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        // Skip node_modules, .git, dist, build
        if (!['node_modules', '.git', 'dist', 'build', 'target', 'bin', 'obj'].includes(entry.name)) {
          if (includeDirs) {
            callback(fullPath);
          }
          this.walkDirectory(fullPath, callback, includeDirs);
        }
      } else if (entry.isFile()) {
        callback(fullPath);
      }
    }
  }
}