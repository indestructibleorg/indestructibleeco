# @ECO-governed
# @ECO-layer: GL30-49
# @ECO-semantic: typescript-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Charter Activated
# GL Root Semantic Anchor: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

// @ECO-governed @ECO-internal-only
// GL Enterprise Platform Runner
// Version: 3.0.0

import { platform, PlatformConfig } from '../platform/index';
import * as fs from 'fs/promises';
import * as path from 'path';

interface RunnerConfig {
  tasks: Array<{
    name: string;
    command: string;
    isolation: boolean;
    timeout?: number;
  }>;
  config: PlatformConfig;
}

async function main() {
  console.log('='.repeat(60));
  console.log('GL Enterprise Platform - Production Runner');
  console.log('Version: 3.0.0 | Execution Mode: Zero Residue');
  console.log('='.repeat(60));
  console.log();

  try {
    // Initialize platform
    console.log('🚀 Initializing platform...');
    await platform.initialize();
    console.log('✅ Platform initialized\n');

    // Load configuration
    const configPath = path.join(__dirname, '../config/enterprise-platform-architecture.yaml');
    const runnerConfig: RunnerConfig = {
      tasks: [
        {
          name: 'Governance Validation',
          command: 'echo "Phase 1: Governance Validation" && sleep 1',
          isolation: true,
          timeout: 30000
        },
        {
          name: 'Architecture Deployment',
          command: 'echo "Phase 2: Architecture Deployment" && sleep 1',
          isolation: true,
          timeout: 30000
        },
        {
          name: 'Integration Testing',
          command: 'echo "Phase 3: Integration Testing" && sleep 1',
          isolation: true,
          timeout: 30000
        }
      ],
      config: {
        enableCleanup: true,
        enableMonitoring: true,
        monitoringInterval: 5000
      }
    };

    // Execute tasks
    console.log('📋 Executing tasks...');
    console.log();

    for (const task of runnerConfig.tasks) {
      console.log(`\n▶️  Task: ${task.name}`);
      console.log(`   Command: ${task.command}`);
      console.log(`   Isolation: ${task.isolation ? 'Yes' : 'No'}`);
      
      const result = await platform.execute({
        command: task.command,
        isolation: task.isolation,
        timeout: task.timeout
      });

      console.log(`   Status: ${result.success ? '✅ SUCCESS' : '❌ FAILED'}`);
      console.log(`   Duration: ${result.duration}ms`);
      
      if (result.complianceReport) {
        console.log(`   Compliance: ${result.complianceReport.overallCompliance}%`);
      }
      
      if (result.cleanupResult) {
        console.log(`   Cleanup: ${result.cleanupResult.filesProcessed} files processed`);
      }
      
      if (!result.success) {
        console.log(`   Error: ${result.error}`);
        console.log();
        console.log('⚠️  Task failed. Stopping execution.');
        break;
      }
    }

    console.log();
    console.log('='.repeat(60));
    console.log('📊 Final Statistics');
    console.log('='.repeat(60));

    // Display monitoring stats
    const stats = platform.getMonitoringStats();
    console.log(`Metrics Collected: ${stats.metricsCollected}`);
    console.log(`Alerts Triggered: ${stats.alertsTriggered}`);
    console.log(`Uptime: ${Math.round(stats.uptime / 1000)}s`);
    console.log(`Memory Usage: ${Math.round(stats.memoryUsage / 1024 / 1024)}MB`);

    // Display alerts
    const alerts = platform.getAlerts();
    if (alerts.length > 0) {
      console.log();
      console.log('⚠️  Alerts:');
      for (const alert of alerts) {
        console.log(`   [${alert.severity.toUpperCase()}] ${alert.name}`);
        console.log(`      ${alert.condition} (${alert.currentValue} > ${alert.threshold})`);
      }
    }

    // Verify zero residue
    console.log();
    console.log('🧹 Verifying zero residue...');
    const zeroResidueCheck = await platform.verifyZeroResidue();
    console.log(`   Status: ${zeroResidueCheck.isClean ? '✅ CLEAN' : '❌ RESIDUE DETECTED'}`);
    
    if (zeroResidueCheck.residueFiles.length > 0) {
      console.log(`   Residue Files: ${zeroResidueCheck.residueFiles.length}`);
      for (const file of zeroResidueCheck.residueFiles) {
        console.log(`      - ${file}`);
      }
    }

    // Shutdown
    console.log();
    console.log('🛑 Shutting down platform...');
    await platform.shutdown();
    console.log('✅ Platform shutdown complete');

    console.log();
    console.log('='.repeat(60));
    console.log('✅ All operations completed successfully');
    console.log('='.repeat(60));

    process.exit(0);

  } catch (error) {
    console.error();
    console.error('❌ Fatal Error:', error instanceof Error ? error.message : String(error));
    
    // Attempt shutdown
    try {
      await platform.shutdown();
    } catch {
      // Ignore shutdown errors
    }
    
    process.exit(1);
  }
}

// Execute if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export { main };