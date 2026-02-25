/**
 * 代碼隔離系統 (Code Isolation System)
 * 功能：備份、隔離虛構文件、清理依賴、驗證編譯
 * 
 * 使用方式:
 * const isolation = new CodeIsolationSystem(projectRoot);
 * const report = await isolation.isolate(hallucinatedFiles);
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { execSync, exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * 隔離操作日誌
 */
export interface IsolationLog {
  timestamp: string;
  action: string;
  status: 'success' | 'warning' | 'error';
  details: string;
  affectedFiles?: string[];
}

/**
 * 隔離報告
 */
export interface IsolationReport {
  timestamp: string;
  projectRoot: string;
  backupPath: string;
  quarantinePath: string;
  quarantineFiles: string[];
  preservedFiles: string[];
  cleanedImportFiles: number;
  compilationStatus: 'success' | 'warning' | 'error';
  compilationErrors: string[];
  logs: IsolationLog[];
  summary: string;
  recoveryInstructions: string[];
}

/**
 * 代碼隔離系統 - 核心類
 */
export class CodeIsolationSystem {
  private projectRoot: string;
  private backupDir: string;
  private quarantineDir: string;
  private logsDir: string;
  private logs: IsolationLog[] = [];
  private timestamp: string;

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
    this.timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.backupDir = path.join(projectRoot, '.recovery', 'backup');
    this.quarantineDir = path.join(projectRoot, '.recovery', 'quarantine');
    this.logsDir = path.join(projectRoot, '.recovery', 'logs');
  }

  /**
   * 執行完整隔離流程
   */
  async isolate(hallucinatedFiles: string[]): Promise<IsolationReport> {
    console.log('🔒 開始代碼隔離流程...\n');

    // 第 1 步：創建恢復目錄結構
    await this.setupRecoveryDirectories();

    // 第 2 步：創建完整備份
    await this.createCompleteBackup();

    // 第 3 步：隔離虛構文件
    const quarantined = await this.quarantineFiles(hallucinatedFiles);

    // 第 4 步：清理虛構導入
    const cleanedCount = await this.cleanImports(hallucinatedFiles);

    // 第 5 步：驗證編譯狀態
    const compilationStatus = await this.verifyCompilation();

    // 第 6 步：獲取保留文件列表
    const preservedFiles = await this.getPreservedFiles();

    // 第 7 步：生成恢復指令
    const recoveryInstructions = this.generateRecoveryInstructions(quarantined);

    // 生成報告
    const report: IsolationReport = {
      timestamp: new Date().toISOString(),
      projectRoot: this.projectRoot,
      backupPath: this.backupDir,
      quarantinePath: this.quarantineDir,
      quarantineFiles: quarantined,
      preservedFiles,
      cleanedImportFiles: cleanedCount,
      compilationStatus,
      compilationErrors: await this.getCompilationErrors(),
      logs: this.logs,
      summary: this.generateSummary(quarantined, cleanedCount, compilationStatus),
      recoveryInstructions,
    };

    // 保存報告
    await this.saveReport(report);

    return report;
  }

  /**
   * 步驟 1：設置恢復目錄結構
   */
  private async setupRecoveryDirectories(): Promise<void> {
    console.log('📂 第 1 步：設置恢復目錄結構...');

    try {
      await fs.mkdir(this.backupDir, { recursive: true });
      await fs.mkdir(this.quarantineDir, { recursive: true });
      await fs.mkdir(this.logsDir, { recursive: true });

      this.addLog('setup_directories', 'success', '恢復目錄結構已創建');
      console.log(`✅ 目錄結構已創建\n`);
    } catch (error) {
      this.addLog('setup_directories', 'error', `目錄創建失敗: ${error}`);
      console.log(`❌ 目錄創建失敗: ${error}\n`);
      throw error;
    }
  }

  /**
   * 步驟 2：創建完整備份
   */
  private async createCompleteBackup(): Promise<void> {
    console.log('💾 第 2 步：創建完整備份...');

    try {
      // 生成帶時間戳的備份路徑
      const backupTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const packagedBackupDir = path.join(this.backupDir, `packages-backup-${backupTimestamp}`);

      // 備份 packages 目錄
      const srcDir = path.join(this.projectRoot, 'packages');
      if (await this.dirExists(srcDir)) {
        execSync(`cp -r ${srcDir} ${packagedBackupDir}`, { stdio: 'ignore' });
        this.addLog('backup_packages', 'success', `已備份 packages 目錄到 ${packagedBackupDir}`);
      }

      // 備份 package.json
      const packageJson = path.join(this.projectRoot, 'package.json');
      if (await this.fileExists(packageJson)) {
        const backupPackageJson = path.join(this.backupDir, 'package.json.backup');
        await fs.copyFile(packageJson, backupPackageJson);
        this.addLog('backup_package_json', 'success', '已備份 package.json');
      }

      // 備份 tsconfig.json
      const tsconfig = path.join(this.projectRoot, 'tsconfig.json');
      if (await this.fileExists(tsconfig)) {
        const backupTsconfig = path.join(this.backupDir, 'tsconfig.json.backup');
        await fs.copyFile(tsconfig, backupTsconfig);
        this.addLog('backup_tsconfig', 'success', '已備份 tsconfig.json');
      }

      // 備份 pnpm-lock.yaml (如果存在)
      const pnpmLock = path.join(this.projectRoot, 'pnpm-lock.yaml');
      if (await this.fileExists(pnpmLock)) {
        const backupLock = path.join(this.backupDir, 'pnpm-lock.yaml.backup');
        await fs.copyFile(pnpmLock, backupLock);
        this.addLog('backup_lock', 'success', '已備份 pnpm-lock.yaml');
      }

      console.log(`✅ 完整備份已創建: ${packagedBackupDir}\n`);
    } catch (error) {
      this.addLog('backup', 'error', `備份失敗: ${error}`);
      console.log(`❌ 備份失敗: ${error}\n`);
      throw error;
    }
  }

  /**
   * 步驟 3：隔離虛構文件
   */
  private async quarantineFiles(files: string[]): Promise<string[]> {
    console.log(`🔐 第 3 步：隔離虛構文件 (${files.length} 個)...\n`);

    const quarantined: string[] = [];

    for (const file of files) {
      try {
        const fullPath = path.join(this.projectRoot, file);
        const quarantinePath = path.join(this.quarantineDir, this.sanitizeFilePath(file));

        // 檢查源文件是否存在
        if (!(await this.fileExists(fullPath))) {
          this.addLog('quarantine_file', 'warning', `文件不存在: ${file}`);
          console.log(`  ⚠️ 文件不存在: ${file}`);
          continue;
        }

        // 複製到隔離區
        await fs.mkdir(path.dirname(quarantinePath), { recursive: true });
        const content = await fs.readFile(fullPath, 'utf-8');
        await fs.writeFile(
          quarantinePath,
          `// QUARANTINED HALLUCINATED CODE\n// Original path: ${file}\n// Quarantine time: ${new Date().toISOString()}\n// DO NOT EXECUTE THIS FILE\n\n${content}`
        );

        // 用標記替換原文件
        await fs.writeFile(
          fullPath,
          `// This file has been quarantined due to hallucinated code\n// Original content is backed up in: .recovery/quarantine/\n// See isolation report for details\n`
        );

        quarantined.push(file);
        this.addLog(
          'quarantine_file',
          'success',
          `已隔離: ${file}`,
          [file]
        );
        console.log(`  ✅ 隔離: ${file}`);
      } catch (error) {
        this.addLog('quarantine_file', 'error', `隔離失敗 ${file}: ${error}`, [file]);
        console.log(`  ❌ 隔離失敗 ${file}: ${error}`);
      }
    }

    console.log(`\n✅ 已隔離 ${quarantined.length} 個文件\n`);
    return quarantined;
  }

  /**
   * 步驟 4：清理虛構導入
   */
  private async cleanImports(hallucinatedFiles: string[]): Promise<number> {
    console.log(`🧹 第 4 步：清理虛構導入...\n`);

    try {
      const { glob } = await import('glob');
      const files = await glob('**/*.{ts,tsx,js,jsx}', {
        cwd: this.projectRoot,
        ignore: ['node_modules/**', 'dist/**', '.recovery/**'],
        absolute: false,
      });

      let cleanedCount = 0;
      const filesModified: string[] = [];

      for (const file of files) {
        try {
          const fullPath = path.join(this.projectRoot, file);
          let content = await fs.readFile(fullPath, 'utf-8');
          let modified = false;

          // 移除指向虛構文件的導入
          for (const hallucinatedFile of hallucinatedFiles) {
            // 構建可能的導入路徑變體
            const basePath = hallucinatedFile.replace(/\.(ts|tsx|js|jsx)$/, '');
            const patterns = [
              new RegExp(`import\\s+[^;]*from\\s+['"]${this.escapeRegex(hallucinatedFile)}['"];?`, 'g'),
              new RegExp(`import\\s+[^;]*from\\s+['"]${this.escapeRegex(basePath)}['"];?`, 'g'),
              new RegExp(`from\\s+['"]${this.escapeRegex(hallucinatedFile)}['"]`, 'g'),
              new RegExp(`from\\s+['"]${this.escapeRegex(basePath)}['"]`, 'g'),
            ];

            for (const pattern of patterns) {
              if (pattern.test(content)) {
                content = content.replace(pattern, '');
                modified = true;
              }
            }
          }

          if (modified) {
            await fs.writeFile(fullPath, content);
            cleanedCount++;
            filesModified.push(file);
          }
        } catch (error) {
          // 忽略讀取錯誤
        }
      }

      this.addLog('clean_imports', 'success', `已清理 ${cleanedCount} 個文件中的虛構導入`, filesModified);
      console.log(`✅ 已清理 ${cleanedCount} 個文件中的虛構導入\n`);

      return cleanedCount;
    } catch (error) {
      this.addLog('clean_imports', 'error', `清理導入失敗: ${error}`);
      console.log(`❌ 清理導入失敗: ${error}\n`);
      return 0;
    }
  }

  /**
   * 步驟 5：驗證編譯狀態
   */
  private async verifyCompilation(): Promise<'success' | 'warning' | 'error'> {
    console.log(`✅ 第 5 步：驗證編譯狀態...\n`);

    try {
      // 嘗試 TypeScript 編譯檢查
      execSync('tsc --noEmit', { cwd: this.projectRoot, stdio: 'pipe' });
      this.addLog('verify_compilation', 'success', 'TypeScript 編譯通過');
      console.log(`✅ TypeScript 編譯通過\n`);
      return 'success';
    } catch (error) {
      // 檢查編譯錯誤數量
      const errorOutput = String(error);
      const errorLines = errorOutput.split('\n').filter((line) => line.includes('error TS'));

      if (errorLines.length > 0 && errorLines.length <= 3) {
        // 少於等於 3 個錯誤時為 warning
        this.addLog(
          'verify_compilation',
          'warning',
          `TypeScript 檢查發現 ${errorLines.length} 個錯誤`
        );
        console.log(
          `⚠️ TypeScript 檢查發現 ${errorLines.length} 個小錯誤，請手動檢查\n`
        );
        return 'warning';
      } else {
        this.addLog('verify_compilation', 'error', `TypeScript 編譯失敗: 超過 3 個錯誤`);
        console.log(`❌ TypeScript 編譯失敗，發現多個錯誤\n`);
        return 'error';
      }
    }
  }

  /**
   * 取得編譯錯誤列表
   */
  private async getCompilationErrors(): Promise<string[]> {
    try {
      execSync('tsc --noEmit', { cwd: this.projectRoot, stdio: 'pipe' });
      return [];
    } catch (error) {
      const output = String(error);
      return output
        .split('\n')
        .filter((line) => line.includes('error TS'))
        .slice(0, 10); // 只返回前 10 個錯誤
    }
  }

  /**
   * 步驟 6：獲取保留文件列表
   */
  private async getPreservedFiles(): Promise<string[]> {
    try {
      const { glob } = await import('glob');
      return await glob('**/*.{ts,tsx,js,jsx}', {
        cwd: this.projectRoot,
        ignore: ['node_modules/**', 'dist/**', '.recovery/**'],
        absolute: false,
      });
    } catch (error) {
      console.warn('⚠️ 獲取文件列表出錯:', error);
      return [];
    }
  }

  /**
   * 步驟 7：生成恢復指令
   */
  private generateRecoveryInstructions(quarantined: string[]): string[] {
    const instructions: string[] = [];

    instructions.push('## 恢復說明');
    instructions.push('');
    instructions.push('如果隔離後發現有誤，可使用以下命令進行恢復：');
    instructions.push('');

    if (quarantined.length > 0) {
      instructions.push('### 完全恢復 (恢復整個 packages 目錄)');
      instructions.push('');
      instructions.push('```bash');
      instructions.push('# 查看最新備份');
      instructions.push('ls -la .recovery/backup/packages-backup-*/');
      instructions.push('');
      instructions.push('# 恢復最新備份');
      instructions.push('rm -rf packages');
      instructions.push('cp -r .recovery/backup/packages-backup-*/ packages');
      instructions.push('pnpm install');
      instructions.push('pnpm run build');
      instructions.push('```');
      instructions.push('');

      instructions.push('### 部分恢復 (只恢復特定文件)');
      instructions.push('');
      instructions.push('```bash');
      for (const file of quarantined.slice(0, 3)) {
        const sanitized = this.sanitizeFilePath(file);
        instructions.push(`cp .recovery/quarantine/${sanitized} ${file}`);
      }
      if (quarantined.length > 3) {
        instructions.push(`# ... 和其他 ${quarantined.length - 3} 個文件`);
      }
      instructions.push('pnpm run build');
      instructions.push('```');
      instructions.push('');

      instructions.push('### 差異比較 (比較原始和隔離版本)');
      instructions.push('');
      instructions.push('```bash');
      instructions.push('cd .recovery');
      instructions.push(`# 列出隔離的文件`);
      instructions.push('ls -la quarantine/');
      instructions.push('```');
    }

    instructions.push('');
    instructions.push('### 確認隔離清單');
    instructions.push('');
    instructions.push('以下文件已被隔離：');
    for (const file of quarantined) {
      instructions.push(`- \`${file}\``);
    }

    return instructions;
  }

  /**
   * 生成隔離摘要
   */
  private generateSummary(
    quarantined: string[],
    cleanedCount: number,
    compilationStatus: string
  ): string {
    const parts: string[] = [];

    parts.push('🔒 隔離摘要');
    parts.push(`- 隔離文件: ${quarantined.length} 個`);
    parts.push(`- 清理導入: ${cleanedCount} 個文件`);
    parts.push(`- 編譯狀態: ${compilationStatus === 'success' ? '✅ 通過' : '⚠️ 需要檢查'}`);

    if (quarantined.length > 0) {
      parts.push('');
      parts.push('已隔離的文件:');
      for (const file of quarantined.slice(0, 5)) {
        parts.push(`- ${file}`);
      }
      if (quarantined.length > 5) {
        parts.push(`- ... 及其他 ${quarantined.length - 5} 個文件`);
      }
    }

    return parts.join('\n');
  }

  /**
   * 保存隔離報告
   */
  private async saveReport(report: IsolationReport): Promise<void> {
    try {
      // 保存 JSON 報告
      const jsonReportPath = path.join(
        this.logsDir,
        `isolation-report-${this.timestamp}.json`
      );
      await fs.writeFile(jsonReportPath, JSON.stringify(report, null, 2));

      // 保存 Markdown 報告
      const markdownReportPath = path.join(
        this.logsDir,
        `isolation-report-${this.timestamp}.md`
      );
      const markdown = this.generateMarkdownReport(report);
      await fs.writeFile(markdownReportPath, markdown);

      this.addLog('save_report', 'success', `報告已保存至 ${this.logsDir}`);
    } catch (error) {
      this.addLog('save_report', 'error', `保存報告失敗: ${error}`);
    }
  }

  /**
   * 生成 Markdown 格式報告
   */
  private generateMarkdownReport(report: IsolationReport): string {
    let markdown = `# 代碼隔離報告\n\n`;
    markdown += `**生成時間**: ${report.timestamp}\n`;
    markdown += `**項目路徑**: \`${report.projectRoot}\`\n\n`;

    markdown += `## 隔離摘要\n\n`;
    markdown += `| 項目 | 數值 |\n`;
    markdown += `|------|------|\n`;
    markdown += `| 隔離文件數 | ${report.quarantineFiles.length} |\n`;
    markdown += `| 清理導入文件 | ${report.cleanedImportFiles} |\n`;
    markdown += `| 保留文件數 | ${report.preservedFiles.length} |\n`;
    markdown += `| 編譯狀態 | ${report.compilationStatus === 'success' ? '✅' : '⚠️'} |\n\n`;

    markdown += `## 隔離的文件清單\n\n`;
    if (report.quarantineFiles.length > 0) {
      report.quarantineFiles.forEach((file) => {
        markdown += `- \`${file}\`\n`;
      });
    } else {
      markdown += `*沒有文件被隔離*\n`;
    }
    markdown += '\n';

    if (report.compilationErrors.length > 0) {
      markdown += `## 編譯錯誤 (前 10 個)\n\n`;
      report.compilationErrors.forEach((error) => {
        markdown += `\`\`\`\n${error}\n\`\`\`\n`;
      });
      markdown += '\n';
    }

    markdown += `## 操作日誌\n\n`;
    report.logs.forEach((log) => {
      const statusIcon =
        log.status === 'success' ? '✅' : log.status === 'warning' ? '⚠️' : '❌';
      markdown += `- ${statusIcon} **${log.action}**: ${log.details}\n`;
    });
    markdown += '\n';

    markdown += `## 恢復指令\n\n`;
    report.recoveryInstructions.forEach((instruction) => {
      markdown += `${instruction}\n`;
    });

    return markdown;
  }

  /**
   * 添加日誌條目
   */
  private addLog(
    action: string,
    status: 'success' | 'warning' | 'error',
    details: string,
    affectedFiles?: string[]
  ): void {
    this.logs.push({
      timestamp: new Date().toISOString(),
      action,
      status,
      details,
      affectedFiles,
    });
  }

  /**
   * 檢查文件是否存在
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 檢查目錄是否存在
   */
  private async dirExists(dirPath: string): Promise<boolean> {
    try {
      const stat = await fs.stat(dirPath);
      return stat.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * 清理文件路徑 (用於隔離區文件名)
   */
  private sanitizeFilePath(filePath: string): string {
    return filePath.replace(/\//g, '_').replace(/\./g, '_');
  }

  /**
   * 轉義正則表達式
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * 打印隔離報告
   */
  printReport(report: IsolationReport): void {
    console.log('\n' + '='.repeat(70));
    console.log('代碼隔離報告');
    console.log('='.repeat(70));

    console.log(`\n📊 隔離統計`);
    console.log(`  隔離文件: ${report.quarantineFiles.length} 個`);
    console.log(`  清理導入: ${report.cleanedImportFiles} 個文件`);
    console.log(`  保留文件: ${report.preservedFiles.length} 個`);
    console.log(`  編譯狀態: ${report.compilationStatus === 'success' ? '✅ 通過' : '⚠️ 需要檢查'}`);

    if (report.quarantineFiles.length > 0) {
      console.log(`\n🔐 隔離的文件`);
      report.quarantineFiles.slice(0, 10).forEach((file) => {
        console.log(`  - ${file}`);
      });
      if (report.quarantineFiles.length > 10) {
        console.log(`  ... 及其他 ${report.quarantineFiles.length - 10} 個文件`);
      }
    }

    console.log(`\n📁 備份位置: ${report.backupPath}`);
    console.log(`📁 隔離位置: ${report.quarantinePath}`);

    console.log(`\n${report.summary}`);

    console.log('\n' + '='.repeat(70) + '\n');
  }
}
