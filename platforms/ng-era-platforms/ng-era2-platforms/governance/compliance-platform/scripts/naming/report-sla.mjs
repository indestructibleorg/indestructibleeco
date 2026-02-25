#!/usr/bin/env node

// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: sla-report-generator
// @GL-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
// @ts-ignore
const axios = (await import('axios')).default;

// SLA Metrics
interface SLAMetrics {
  ncr: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    resolved_24h: number;
  };
  vfc: {
    total: number;
    compliance_rate: number;
    passed: number;
    failed: number;
  };
  mfr: {
    total: number;
    success_rate: number;
    success: number;
    failure: number;
  };
  ars: {
    total: number;
    resolution_rate: number;
    avg_resolution_time: number;
  };
}

// Fetch metrics from Prometheus
async function fetchPrometheusMetrics(prometheusUrl: string): Promise<any> {
  try {
    const response = await axios.get(`${prometheusUrl}/api/v1/query`, {
      params: {
        query: 'sum(naming_violations_total)'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching Prometheus metrics:', error);
    return null;
  }
}

// Calculate SLA metrics
function calculateSLAMetrics(metricsData: any): SLAMetrics {
  // Placeholder implementation - in production, this would parse actual Prometheus data
  return {
    ncr: {
      total: metricsData?.ncr_total || 0,
      critical: metricsData?.ncr_critical || 0,
      high: metricsData?.ncr_high || 0,
      medium: metricsData?.ncr_medium || 0,
      low: metricsData?.ncr_low || 0,
      resolved_24h: metricsData?.ncr_resolved_24h || 0
    },
    vfc: {
      total: metricsData?.vfc_total || 0,
      compliance_rate: metricsData?.vfc_compliance_rate || 0,
      passed: metricsData?.vfc_passed || 0,
      failed: metricsData?.vfc_failed || 0
    },
    mfr: {
      total: metricsData?.mfr_total || 0,
      success_rate: metricsData?.mfr_success_rate || 0,
      success: metricsData?.mfr_success || 0,
      failure: metricsData?.mfr_failure || 0
    },
    ars: {
      total: metricsData?.ars_total || 0,
      resolution_rate: metricsData?.ars_resolution_rate || 0,
      avg_resolution_time: metricsData?.ars_avg_resolution_time || 0
    }
  };
}

// Generate SLA report
function generateSLAReport(metrics: SLAMetrics): string {
  const report = {
    timestamp: new Date().toISOString(),
    report_type: 'sla_metrics',
    summary: {
      overall_compliance: calculateOverallCompliance(metrics),
      status: determineOverallStatus(metrics)
    },
    metrics: metrics,
    trends: {
      ncr_trend: calculateTrend(metrics.ncr.total, metrics.ncr.resolved_24h),
      vfc_trend: calculateTrend(metrics.vfc.passed, metrics.vfc.failed),
      mfr_trend: calculateTrend(metrics.mfr.success, metrics.mfr.failure)
    },
    recommendations: generateRecommendations(metrics)
  };

  return JSON.stringify(report, null, 2);
}

// Calculate overall compliance
function calculateOverallCompliance(metrics: SLAMetrics): number {
  const ncr_compliance = 1 - (metrics.ncr.total / (metrics.ncr.total + 100)); // Normalized
  const vfc_compliance = metrics.vfc.compliance_rate / 100;
  const mfr_compliance = metrics.mfr.success_rate / 100;
  
  return Math.round((ncr_compliance + vfc_compliance + mfr_compliance) / 3 * 100);
}

// Determine overall status
function determineOverallStatus(metrics: SLAMetrics): string {
  const compliance = calculateOverallCompliance(metrics);
  if (compliance >= 99) return 'healthy';
  if (compliance >= 95) return 'warning';
  return 'critical';
}

// Calculate trend
function calculateTrend(positive: number, negative: number): string {
  if (positive > negative) return 'improving';
  if (positive < negative) return 'degrading';
  return 'stable';
}

// Generate recommendations
function generateRecommendations(metrics: SLAMetrics): string[] {
  const recommendations: string[] = [];
  
  if (metrics.ncr.critical > 0) {
    recommendations.push('⚠️ Critical NCRs detected - immediate attention required');
  }
  
  if (metrics.vfc.compliance_rate < 95) {
    recommendations.push('📉 VFC compliance rate below 95% - review and fix violations');
  }
  
  if (metrics.mfr.success_rate < 90) {
    recommendations.push('🔧 MFR success rate below 90% - review auto-fix configurations');
  }
  
  if (metrics.ars.resolution_rate < 95) {
    recommendations.push('⏱️ ARS resolution rate below 95% - improve response times');
  }
  
  if (recommendations.length === 0) {
    recommendations.push('✅ All SLA metrics within acceptable range');
  }
  
  return recommendations;
}

// Save report to file
function saveReport(report: string, outputPath: string): void {
  const dir = join(process.cwd(), outputPath);
  mkdirSync(dir, { recursive: true });
  
  const filePath = join(dir, `sla-metrics-${Date.now()}.json`);
  writeFileSync(filePath, report);
  
  console.log(`SLA report saved to: ${filePath}`);
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const command = args[0];
  
  switch (command) {
    case 'generate':
      const prometheusUrl = args[1] || 'http://localhost:9090';
      const outputPath = args[2] || 'artifacts/reports/sla';
      
      console.log('Generating SLA report...');
      
      fetchPrometheusMetrics(prometheusUrl)
        .then(data => {
          const metrics = calculateSLAMetrics(data?.data || {});
          const report = generateSLAReport(metrics);
          saveReport(report, outputPath);
          console.log('✅ SLA report generated successfully');
        })
        .catch(error => {
          console.error('Error generating SLA report:', error);
          process.exit(1);
        });
      break;
    
    default:
      console.log('Usage: node report-sla.mjs generate [prometheus-url] [output-path]');
      process.exit(1);
  }
}

export { generateSLAReport, calculateSLAMetrics, SLAMetrics };