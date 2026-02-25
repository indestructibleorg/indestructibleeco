# @ECO-governed
# @ECO-layer: GL20-29
# @ECO-semantic: typescript-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Charter Activated
# GL Root Semantic Anchor: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-platform-universe/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

// @ECO-governed @ECO-internal-only
// Production-grade Internal Monitoring System
// Version: 3.0.0

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';

export interface Metric {
  name: string;
  value: number;
  timestamp: number;
  labels?: Record<string, string>;
}

export interface Alert {
  alertId: string;
  name: string;
  severity: 'critical' | 'warning' | 'info';
  condition: string;
  currentValue: number;
  threshold: number;
  timestamp: number;
}

export interface MonitoringStats {
  metricsCollected: number;
  alertsTriggered: number;
  uptime: number;
  memoryUsage: number;
}

export class InternalMonitor extends EventEmitter {
  private metrics: Map<string, Metric[]> = new Map();
  private alerts: Alert[] = [];
  private startTime: number;
  private maxMetricsPerKey: number = 1000;
  private monitoringInterval?: NodeJS.Timeout;

  constructor() {
    super();
    this.startTime = Date.now();
  }

  /**
   * Start monitoring
   */
  start(intervalMs: number = 10000): void {
    if (this.monitoringInterval) {
      return;
    }

    this.monitoringInterval = setInterval(() => {
      this.collectSystemMetrics();
    }, intervalMs);

    this.emit('started');
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    this.emit('stopped');
  }

  /**
   * Record metric
   */
  recordMetric(metric: Omit<Metric, 'timestamp'>): void {
    const fullMetric: Metric = {
      ...metric,
      timestamp: Date.now()
    };

    if (!this.metrics.has(metric.name)) {
      this.metrics.set(metric.name, []);
    }

    const metricsArray = this.metrics.get(metric.name)!;
    metricsArray.push(fullMetric);

    // Keep only recent metrics
    if (metricsArray.length > this.maxMetricsPerKey) {
      metricsArray.shift();
    }

    this.emit('metric', fullMetric);
  }

  /**
   * Collect system metrics
   */
  private collectSystemMetrics(): void {
    const memoryUsage = process.memoryUsage();
    
    this.recordMetric({
      name: 'memory_usage_bytes',
      value: memoryUsage.heapUsed,
      labels: { type: 'heap' }
    });

    this.recordMetric({
      name: 'memory_total_bytes',
      value: memoryUsage.heapTotal,
      labels: { type: 'total' }
    });

    this.recordMetric({
      name: 'uptime_seconds',
      value: Math.floor((Date.now() - this.startTime) / 1000)
    });

    // Check for memory usage alert
    const memoryPercent = (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100;
    if (memoryPercent > 90) {
      this.triggerAlert({
        alertId: uuidv4(),
        name: 'high_memory_usage',
        severity: 'warning',
        condition: 'memory_usage > 90%',
        currentValue: memoryPercent,
        threshold: 90,
        timestamp: Date.now()
      });
    }
  }

  /**
   * Trigger alert
   */
  private triggerAlert(alert: Alert): void {
    this.alerts.push(alert);
    this.emit('alert', alert);
  }

  /**
   * Get metrics by name
   */
  getMetrics(name: string): Metric[] {
    return this.metrics.get(name) || [];
  }

  /**
   * Get latest metric
   */
  getLatestMetric(name: string): Metric | undefined {
    const metrics = this.getMetrics(name);
    return metrics.length > 0 ? metrics[metrics.length - 1] : undefined;
  }

  /**
   * Get metrics statistics
   */
  getMetricStats(name: string): { min: number; max: number; avg: number; count: number } | undefined {
    const metrics = this.getMetrics(name);
    if (metrics.length === 0) {
      return undefined;
    }

    const values = metrics.map(m => m.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;

    return {
      min,
      max,
      avg,
      count: metrics.length
    };
  }

  /**
   * Get all alerts
   */
  getAlerts(): Alert[] {
    return [...this.alerts];
  }

  /**
   * Get alerts by severity
   */
  getAlertsBySeverity(severity: 'critical' | 'warning' | 'info'): Alert[] {
    return this.alerts.filter(a => a.severity === severity);
  }

  /**
   * Get monitoring statistics
   */
  getStats(): MonitoringStats {
    let metricsCollected = 0;
    for (const metricsArray of this.metrics.values()) {
      metricsCollected += metricsArray.length;
    }

    const memoryUsage = process.memoryUsage();

    return {
      metricsCollected,
      alertsTriggered: this.alerts.length,
      uptime: Date.now() - this.startTime,
      memoryUsage: memoryUsage.heapUsed
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics.clear();
  }

  /**
   * Clear all alerts
   */
  clearAlerts(): void {
    this.alerts = [];
  }

  /**
   * Export metrics (internal use only)
   */
  exportMetrics(): Record<string, Metric[]> {
    const exported: Record<string, Metric[]> = {};
    for (const [key, value] of this.metrics.entries()) {
      exported[key] = [...value];
    }
    return exported;
  }
}