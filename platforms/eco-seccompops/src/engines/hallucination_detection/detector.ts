/**
 * 虛構代碼檢測引擎 (Hallucination Detection Engine)
 * 支持五層檢測框架：虛假 API、未導入符號、循環依賴、孤立代碼、邏輯缺陷
 * 
 * 使用方式:
 * const detector = new HallucinationDetector(projectRoot);
 * const report = await detector.scanProject();
 * detector.printReport(report);
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { glob } from 'glob';
import * as ts from 'typescript';

/**
 * 虛構代碼指標定義
 */
export interface HallucinationIndicator {
  type: 'missing_import' | 'undefined_function' | 'broken_logic' | 'fake_api' | 'circular' | 'orphaned';
  severity: 'critical' | 'high' | 'medium' | 'low';
  file: string;
  line: number;
  column: number;
  content: string;
  reason: string;
  suggestion?: string;
}

/**
 * 虛構代碼檢測報告
 */
export interface HallucinationReport {
  timestamp: string;
  projectRoot: string;
  totalFiles: number;
  totalIndicators: number;
  critical: HallucinationIndicator[];
  high: HallucinationIndicator[];
  medium: HallucinationIndicator[];
  low: HallucinationIndicator[];
  summary: string;
  executionTime: number;
  detectionDetails: {
    fakeApiPatterns: number;
    undefinedSymbols: number;
    brokenLogic: number;
    orphanedCode: number;
    circularDeps: number;
  };
}

/**
 * 符號表 - 追蹤導入、導出、定義
 */
interface SymbolTable {
  imports: Map<string, string>;  // 符號名 -> 來源路徑
  exports: Map<string, boolean>; // 符號名 -> 是否被使用
  definitions: Map<string, string>; // 符號名 -> 定義位置
  builtins: Set<string>;
}

/**
 * 依賴圖節點
 */
interface DependencyNode {
  file: string;
  imports: Set<string>;
  dependents: Set<string>;
  visited?: boolean;
  visitPath?: string[];
}

/**
 * 虛構代碼檢測引擎 - 核心類
 */
export class HallucinationDetector {
  private projectRoot: string;
  private indicators: HallucinationIndicator[] = [];
  private fileCache: Map<string, string> = new Map();
  private symbolTables: Map<string, SymbolTable> = new Map();
  private dependencyGraph: Map<string, DependencyNode> = new Map();
  private startTime: number = 0;

  // 內置函數和全局對象
  private builtins = new Set([
    'console',
    'Array',
    'Object',
    'String',
    'Number',
    'Boolean',
    'Date',
    'Math',
    'JSON',
    'Promise',
    'Map',
    'Set',
    'WeakMap',
    'WeakSet',
    'Proxy',
    'Reflect',
    'Symbol',
    'BigInt',
    'Intl',
    'Error',
    'TypeError',
    'ReferenceError',
    'SyntaxError',
    'RangeError',
    'setTimeout',
    'setInterval',
    'clearTimeout',
    'clearInterval',
    'parseInt',
    'parseFloat',
    'isNaN',
    'isFinite',
    'encodeURI',
    'decodeURI',
    'encodeURIComponent',
    'decodeURIComponent',
    'Buffer',
    'process',
    'global',
    'require',
    'module',
    'exports',
  ]);

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
  }

  /**
   * 執行完整的項目掃描
   */
  async scanProject(): Promise<HallucinationReport> {
    this.startTime = Date.now();
    this.indicators = [];
    this.fileCache.clear();
    this.symbolTables.clear();
    this.dependencyGraph.clear();

    console.log('🔍 掃描虛構代碼...\n');

    // 第 1 步：收集所有文件
    const files = await this.collectFiles();
    console.log(`📁 檢查 ${files.length} 個文件\n`);

    // 第 2 步：加載和快取所有文件內容
    console.log('📖 加載文件內容...');
    await this.loadFilesIntoCache(files);
    console.log(`✅ 已加載 ${files.length} 個文件\n`);

    // 第 3 步：構建符號表
    console.log('🏗️ 構建符號表...');
    await this.buildSymbolTables(files);
    console.log(`✅ 符號表完成\n`);

    // 第 4 步：構建依賴圖
    console.log('🔗 構建依賴圖...');
    await this.buildDependencyGraph(files);
    console.log(`✅ 依賴圖完成\n`);

    // 第 5 步：執行五層檢測 (並行)
    console.log('🔎 執行五層檢測...\n');

    await Promise.all([
      this.detectFakeAPIs(files),
      this.detectUndefinedSymbols(files),
      this.detectBrokenLogic(files),
      this.detectOrphanedCode(files),
      this.detectCircularDependencies(files),
    ]);

    console.log('✅ 檢測完成\n');

    // 生成報告
    const report = this.generateReport(files.length);
    const executionTime = Date.now() - this.startTime;
    report.executionTime = executionTime;

    return report;
  }

  /**
   * 第 1 層：收集所有項目文件
   */
  private async collectFiles(): Promise<string[]> {
    try {
      const files = await glob('**/*.{ts,tsx,js,jsx}', {
        cwd: this.projectRoot,
        ignore: [
          'node_modules/**',
          'dist/**',
          '.next/**',
          'build/**',
          '*.d.ts',
          '.recovery/**',
        ],
        absolute: false,
      });
      return files;
    } catch (error) {
      console.warn('⚠️ 收集文件出錯:', error);
      return [];
    }
  }

  /**
   * 加載所有文件內容到快取
   */
  private async loadFilesIntoCache(files: string[]): Promise<void> {
    for (const file of files) {
      try {
        const fullPath = path.join(this.projectRoot, file);
        const content = await fs.readFile(fullPath, 'utf-8');
        this.fileCache.set(file, content);
      } catch (error) {
        // 忽略讀取錯誤
      }
    }
  }

  /**
   * 第 2 層：構建符號表 (每個文件一個)
   */
  private async buildSymbolTables(files: string[]): Promise<void> {
    for (const file of files) {
      const content = this.fileCache.get(file);
      if (!content) continue;

      const symbolTable: SymbolTable = {
        imports: new Map(),
        exports: new Map(),
        definitions: new Map(),
        builtins: this.builtins,
      };

      // 提取導入
      const importRegex = /import\s+(?:{([^}]+)}|(\*\s+as\s+(\w+))|(\w+))\s+from\s+['"]([^'"]+)['"]/g;
      let match;
      while ((match = importRegex.exec(content)) !== null) {
        if (match[1]) {
          // Named imports: { a, b }
          match[1].split(',').forEach((item) => {
            const [name] = item.trim().split(' as ');
            symbolTable.imports.set(name.trim(), match[5]);
          });
        } else if (match[3]) {
          // Namespace import: * as name
          symbolTable.imports.set(match[3], match[5]);
        } else if (match[4]) {
          // Default import
          symbolTable.imports.set(match[4], match[5]);
        }
      }

      // 提取導出
      const exportRegex = /export\s+(?:async\s+)?(?:function|const|class|interface|type)\s+(\w+)/g;
      while ((match = exportRegex.exec(content)) !== null) {
        symbolTable.exports.set(match[1], false); // 初始化為未使用
      }

      // 提取函數定義
      const functionRegex = /(?:function|const)\s+(\w+)\s*(?:=|:)/g;
      while ((match = functionRegex.exec(content)) !== null) {
        symbolTable.definitions.set(match[1], file);
      }

      this.symbolTables.set(file, symbolTable);
    }

    // 標記被使用的導出
    for (const [file, symbolTable] of this.symbolTables.entries()) {
      const content = this.fileCache.get(file) || '';
      for (const exportName of symbolTable.exports.keys()) {
        const callRegex = new RegExp(`\\b${exportName}\\s*\\(`, 'g');
        const callCount = (content.match(callRegex) || []).length;
        if (callCount > 1) {
          // 導出定義出現 + 至少一次調用
          symbolTable.exports.set(exportName, true);
        }
      }
    }
  }

  /**
   * 第 3 層：構建依賴圖
   */
  private async buildDependencyGraph(files: string[]): Promise<void> {
    for (const file of files) {
      const content = this.fileCache.get(file);
      if (!content) continue;

      const node: DependencyNode = {
        file,
        imports: new Set(),
        dependents: new Set(),
      };

      // 收集導入
      const importRegex = /from\s+['"]([^'"]+)['"]/g;
      let match;
      while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1];
        // 解析相對路徑為絕對文件路徑
        if (importPath.startsWith('.')) {
          const resolvedPath = this.resolveImportPath(file, importPath);
          node.imports.add(resolvedPath);
        }
      }

      this.dependencyGraph.set(file, node);
    }

    // 構建反向依賴
    for (const [file, node] of this.dependencyGraph.entries()) {
      for (const dependency of node.imports) {
        const dependencyNode = this.dependencyGraph.get(dependency);
        if (dependencyNode) {
          dependencyNode.dependents.add(file);
        }
      }
    }
  }

  /**
   * 檢測 1：虛假 API 調用
   */
  private async detectFakeAPIs(files: string[]): Promise<void> {
    const fakePatterns = [
      { pattern: /api\.fake\./gi, name: 'api.fake' },
      { pattern: /\.mock\./gi, name: '.mock' },
      { pattern: /TODO_IMPLEMENT/gi, name: 'TODO_IMPLEMENT' },
      { pattern: /PLACEHOLDER/gi, name: 'PLACEHOLDER' },
      { pattern: /TODO:\s*implement/gi, name: 'TODO: implement' },
      { pattern: /FIXME:\s*implement/gi, name: 'FIXME: implement' },
      { pattern: /this\.notImplemented\(\)/gi, name: 'notImplemented()' },
    ];

    for (const file of files) {
      const content = this.fileCache.get(file);
      if (!content) continue;

      const lines = content.split('\n');
      lines.forEach((line, lineNum) => {
        fakePatterns.forEach((pattern) => {
          let match;
          while ((match = pattern.pattern.exec(line)) !== null) {
            this.indicators.push({
              type: 'fake_api',
              severity: 'critical',
              file,
              line: lineNum + 1,
              column: match.index + 1,
              content: line.trim(),
              reason: `檢測到虛假 API 調用: ${pattern.name}`,
              suggestion: `移除此虛構代碼，使用真實 API`,
            });
          }
        });
      });
    }
  }

  /**
   * 檢測 2：未導入或未定義的符號
   */
  private async detectUndefinedSymbols(files: string[]): Promise<void> {
    for (const file of files) {
      const content = this.fileCache.get(file);
      if (!content) continue;

      const symbolTable = this.symbolTables.get(file);
      if (!symbolTable) continue;

      const lines = content.split('\n');

      // 尋找函數調用
      const callRegex = /\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(/g;
      lines.forEach((line, lineNum) => {
        let match;
        while ((match = callRegex.exec(line)) !== null) {
          const funcName = match[1];

          // 檢查是否是已知符號
          const isKnown =
            symbolTable.imports.has(funcName) ||
            symbolTable.definitions.has(funcName) ||
            symbolTable.builtins.has(funcName) ||
            this.isCommonGlobal(funcName);

          if (!isKnown) {
            // 檢查是否是方法調用 (忽略 this.xxx() 和 obj.xxx())
            const beforeMatch = line.substring(Math.max(0, match.index - 5), match.index);
            if (!beforeMatch.includes('.')) {
              this.indicators.push({
                type: 'undefined_function',
                severity: 'high',
                file,
                line: lineNum + 1,
                column: match.index + 1,
                content: line.trim(),
                reason: `函數 "${funcName}" 未被導入或定義`,
                suggestion: `導入此函數或確保其已定義`,
              });
            }
          }
        }
      });
    }
  }

  /**
   * 檢測 3：邏輯缺陷
   */
  private async detectBrokenLogic(files: string[]): Promise<void> {
    const brokenPatterns = [
      {
        pattern: /if\s*\(\s*true\s*\)/gi,
        reason: '無條件的 if(true) 語句',
        severity: 'high' as const,
      },
      {
        pattern: /if\s*\(\s*false\s*\)/gi,
        reason: '永遠不會執行的 if(false) 語句',
        severity: 'medium' as const,
      },
      {
        pattern: /return\s+undefined/gi,
        reason: '顯式返回 undefined（應使用隱式返回）',
        severity: 'low' as const,
      },
      {
        pattern: /throw\s+new\s+Error\(\s*\)/gi,
        reason: '拋出空錯誤訊息',
        severity: 'medium' as const,
      },
      {
        pattern: /\/\/\s*TODO\b/gi,
        reason: '未完成的代碼標記 (TODO)',
        severity: 'low' as const,
      },
      {
        pattern: /\/\/\s*FIXME\b/gi,
        reason: '需要修復的代碼標記 (FIXME)',
        severity: 'low' as const,
      },
      {
        pattern: /while\s*\(\s*true\s*\)/gi,
        reason: '無限循環 (while true)',
        severity: 'high' as const,
      },
    ];

    for (const file of files) {
      const content = this.fileCache.get(file);
      if (!content) continue;

      const lines = content.split('\n');
      lines.forEach((line, lineNum) => {
        brokenPatterns.forEach((pattern) => {
          let match;
          while ((match = pattern.pattern.exec(line)) !== null) {
            this.indicators.push({
              type: 'broken_logic',
              severity: pattern.severity,
              file,
              line: lineNum + 1,
              column: match.index + 1,
              content: line.trim(),
              reason: pattern.reason,
            });
          }
        });
      });
    }
  }

  /**
   * 檢測 4：孤立代碼
   */
  private async detectOrphanedCode(files: string[]): Promise<void> {
    for (const file of files) {
      const symbolTable = this.symbolTables.get(file);
      if (!symbolTable) continue;

      for (const [exportName, isUsed] of symbolTable.exports.entries()) {
        if (!isUsed) {
          const content = this.fileCache.get(file) || '';
          const lines = content.split('\n');

          // 找到導出定義的行
          for (let lineNum = 0; lineNum < lines.length; lineNum++) {
            const line = lines[lineNum];
            if (line.includes(`export`) && line.includes(exportName)) {
              this.indicators.push({
                type: 'orphaned',
                severity: 'low',
                file,
                line: lineNum + 1,
                column: 1,
                content: line.trim(),
                reason: `導出的 "${exportName}" 似乎未被使用`,
                suggestion: `移除此導出或確保其被導入使用`,
              });
              break;
            }
          }
        }
      }
    }
  }

  /**
   * 檢測 5：循環依賴
   */
  private async detectCircularDependencies(files: string[]): Promise<void> {
    const visitedGlobal = new Set<string>();

    for (const startFile of files) {
      if (visitedGlobal.has(startFile)) continue;

      const path: string[] = [];
      const visited = new Set<string>();

      const dfs = (file: string): void => {
        if (visited.has(file)) {
          // 找到循環
          const cycleStart = path.indexOf(file);
          if (cycleStart !== -1) {
            const cycle = path.slice(cycleStart).concat(file);
            this.indicators.push({
              type: 'circular',
              severity: 'high',
              file: startFile,
              line: 1,
              column: 1,
              content: `Circular: ${cycle.join(' → ')}`,
              reason: `檢測到循環依賴: ${cycle.join(' → ')}`,
            });
          }
          return;
        }

        visited.add(file);
        path.push(file);
        visitedGlobal.add(file);

        const node = this.dependencyGraph.get(file);
        if (node) {
          for (const dep of node.imports) {
            dfs(dep);
          }
        }

        path.pop();
      };

      dfs(startFile);
    }
  }

  /**
   * 檢查是否是常見全局函數
   */
  private isCommonGlobal(name: string): boolean {
    const commonGlobals = new Set([
      'fetch',
      'fetch',
      'async',
      'await',
      'useState',
      'useEffect',
      'useContext',
      'useReducer',
      'useCallback',
      'useMemo',
      'useRef',
      'describe',
      'it',
      'test',
      'expect',
      'beforeEach',
      'afterEach',
      'beforeAll',
      'afterAll',
    ]);
    return commonGlobals.has(name);
  }

  /**
   * 解析導入路徑為絕對文件路徑
   */
  private resolveImportPath(sourceFile: string, importPath: string): string {
    const sourceDir = path.dirname(sourceFile);
    const resolved = path.normalize(path.join(sourceDir, importPath));

    // 嘗試多種擴展名
    const extensions = ['.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx'];
    for (const ext of extensions) {
      const fullPath = resolved + (ext.startsWith('/') ? '' : ext);
      if (this.fileCache.has(fullPath) || this.fileCache.has(resolved)) {
        return this.fileCache.has(fullPath) ? fullPath : resolved;
      }
    }

    return resolved;
  }

  /**
   * 生成檢測報告
   */
  private generateReport(totalFiles: number): HallucinationReport {
    // 按嚴重級別分類
    const critical = this.indicators.filter((i) => i.severity === 'critical');
    const high = this.indicators.filter((i) => i.severity === 'high');
    const medium = this.indicators.filter((i) => i.severity === 'medium');
    const low = this.indicators.filter((i) => i.severity === 'low');

    // 生成摘要
    const summary =
      critical.length > 0
        ? `🚨 發現 ${critical.length} 個關鍵虛構代碼，需要立即清理`
        : high.length > 0
          ? `⚠️ 發現 ${high.length} 個高優先級問題`
          : `✅ 代碼質量良好`;

    // 統計檢測類型
    const detectionDetails = {
      fakeApiPatterns: this.indicators.filter((i) => i.type === 'fake_api').length,
      undefinedSymbols: this.indicators.filter((i) => i.type === 'undefined_function').length,
      brokenLogic: this.indicators.filter((i) => i.type === 'broken_logic').length,
      orphanedCode: this.indicators.filter((i) => i.type === 'orphaned').length,
      circularDeps: this.indicators.filter((i) => i.type === 'circular').length,
    };

    return {
      timestamp: new Date().toISOString(),
      projectRoot: this.projectRoot,
      totalFiles,
      totalIndicators: this.indicators.length,
      critical,
      high,
      medium,
      low,
      summary,
      executionTime: 0, // 稍後填充
      detectionDetails,
    };
  }

  /**
   * 打印檢測報告
   */
  printReport(report: HallucinationReport): void {
    console.log('\n' + '='.repeat(70));
    console.log('虛構代碼檢測報告');
    console.log('='.repeat(70));

    console.log(`\n📊 統計信息`);
    console.log(`  掃描文件: ${report.totalFiles}`);
    console.log(`  發現問題: ${report.totalIndicators}`);
    console.log(`  🔴 關鍵: ${report.critical.length}`);
    console.log(`  🟠 高: ${report.high.length}`);
    console.log(`  🟡 中: ${report.medium.length}`);
    console.log(`  🟢 低: ${report.low.length}`);
    console.log(`  ⏱️ 執行時間: ${(report.executionTime / 1000).toFixed(2)}s`);

    console.log(`\n🔍 檢測類型統計`);
    console.log(`  虛假 API: ${report.detectionDetails.fakeApiPatterns}`);
    console.log(`  未定義符號: ${report.detectionDetails.undefinedSymbols}`);
    console.log(`  邏輯缺陷: ${report.detectionDetails.brokenLogic}`);
    console.log(`  孤立代碼: ${report.detectionDetails.orphanedCode}`);
    console.log(`  循環依賴: ${report.detectionDetails.circularDeps}`);

    if (report.critical.length > 0) {
      console.log(`\n🔴 關鍵問題 (${report.critical.length})`);
      report.critical.slice(0, 10).forEach((indicator) => {
        console.log(`\n  [${indicator.file}:${indicator.line}:${indicator.column}]`);
        console.log(`  類型: ${indicator.type}`);
        console.log(`  原因: ${indicator.reason}`);
        console.log(`  代碼: ${indicator.content}`);
        if (indicator.suggestion) {
          console.log(`  建議: ${indicator.suggestion}`);
        }
      });
      if (report.critical.length > 10) {
        console.log(`\n  ... 還有 ${report.critical.length - 10} 個關鍵問題`);
      }
    }

    if (report.high.length > 0) {
      console.log(`\n🟠 高優先級問題 (${report.high.length})`);
      report.high.slice(0, 5).forEach((indicator) => {
        console.log(`  [${indicator.file}:${indicator.line}] ${indicator.reason}`);
      });
      if (report.high.length > 5) {
        console.log(`  ... 還有 ${report.high.length - 5} 個高優先級問題`);
      }
    }

    console.log(`\n📋 總結: ${report.summary}`);
    console.log('='.repeat(70) + '\n');
  }

  /**
   * 保存報告為 JSON
   */
  async saveReportAsJSON(report: HallucinationReport, outputPath: string): Promise<void> {
    try {
      await fs.mkdir(path.dirname(outputPath), { recursive: true });
      await fs.writeFile(outputPath, JSON.stringify(report, null, 2), 'utf-8');
      console.log(`✅ JSON 報告已保存: ${outputPath}`);
    } catch (error) {
      console.error(`❌ 保存 JSON 報告失敗:`, error);
    }
  }

  /**
   * 保存報告為 Markdown
   */
  async saveReportAsMarkdown(report: HallucinationReport, outputPath: string): Promise<void> {
    try {
      let markdown = `# 虛構代碼檢測報告\n\n`;
      markdown += `**生成時間**: ${report.timestamp}\n`;
      markdown += `**執行時間**: ${(report.executionTime / 1000).toFixed(2)}s\n\n`;

      markdown += `## 統計摘要\n\n`;
      markdown += `| 指標 | 數量 |\n`;
      markdown += `|------|------|\n`;
      markdown += `| 掃描文件 | ${report.totalFiles} |\n`;
      markdown += `| 總問題數 | ${report.totalIndicators} |\n`;
      markdown += `| 🔴 關鍵 | ${report.critical.length} |\n`;
      markdown += `| 🟠 高 | ${report.high.length} |\n`;
      markdown += `| 🟡 中 | ${report.medium.length} |\n`;
      markdown += `| 🟢 低 | ${report.low.length} |\n\n`;

      markdown += `## 檢測類型統計\n\n`;
      markdown += `| 檢測類型 | 數量 |\n`;
      markdown += `|---------|------|\n`;
      markdown += `| 虛假 API | ${report.detectionDetails.fakeApiPatterns} |\n`;
      markdown += `| 未定義符號 | ${report.detectionDetails.undefinedSymbols} |\n`;
      markdown += `| 邏輯缺陷 | ${report.detectionDetails.brokenLogic} |\n`;
      markdown += `| 孤立代碼 | ${report.detectionDetails.orphanedCode} |\n`;
      markdown += `| 循環依賴 | ${report.detectionDetails.circularDeps} |\n\n`;

      // 詳細問題列表
      if (report.critical.length > 0) {
        markdown += `## 🔴 關鍵問題\n\n`;
        report.critical.forEach((indicator, index) => {
          markdown += `### 問題 ${index + 1}\n\n`;
          markdown += `- **文件**: \`${indicator.file}\`\n`;
          markdown += `- **位置**: 第 ${indicator.line} 行，第 ${indicator.column} 列\n`;
          markdown += `- **類型**: ${indicator.type}\n`;
          markdown += `- **原因**: ${indicator.reason}\n`;
          markdown += `- **代碼**: \`\`\`\n${indicator.content}\n\`\`\`\n`;
          if (indicator.suggestion) {
            markdown += `- **建議**: ${indicator.suggestion}\n`;
          }
          markdown += '\n';
        });
      }

      if (report.high.length > 0) {
        markdown += `## 🟠 高優先級問題\n\n`;
        report.high.forEach((indicator, index) => {
          markdown += `- [${indicator.file}:${indicator.line}] ${indicator.reason}\n`;
        });
        markdown += '\n';
      }

      markdown += `## 總結\n\n${report.summary}\n`;

      await fs.mkdir(path.dirname(outputPath), { recursive: true });
      await fs.writeFile(outputPath, markdown, 'utf-8');
      console.log(`✅ Markdown 報告已保存: ${outputPath}`);
    } catch (error) {
      console.error(`❌ 保存 Markdown 報告失敗:`, error);
    }
  }

  /**
   * 生成可修復的建議列表
   */
  generateRemediationPlan(report: HallucinationReport): string[] {
    const plan: string[] = [];

    if (report.critical.length > 0) {
      plan.push(`🔴 P0 - 立即隔離虛構文件 (${report.critical.length} 個)`);
      const filesToIsolate = new Set(report.critical.map((i) => i.file));
      for (const file of filesToIsolate) {
        plan.push(`  - 隔離: ${file}`);
      }
    }

    if (report.high.length > 0) {
      plan.push(`🟠 P1 - 修復高優先級問題 (${report.high.length} 個)`);
      plan.push(`  - 檢查未導入的符號`);
      plan.push(`  - 解決循環依賴`);
    }

    if (report.medium.length > 0) {
      plan.push(`🟡 P2 - 修復邏輯缺陷 (${report.medium.length} 個)`);
      plan.push(`  - 修復 if/while 邏輯`);
      plan.push(`  - 改進錯誤處理`);
    }

    if (report.low.length > 0) {
      plan.push(`🟢 P3 - 清理孤立代碼 (${report.low.length} 個)`);
      plan.push(`  - 移除未使用的導出`);
      plan.push(`  - 清理 TODO 標記`);
    }

    return plan;
  }
}
