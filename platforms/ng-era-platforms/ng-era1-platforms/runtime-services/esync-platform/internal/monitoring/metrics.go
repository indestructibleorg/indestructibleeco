// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: esync-platform-source
// @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
//
// GL Unified Charter Activated
/**
 * @GL-governed
 * @GL-layer: esync-platform
 * @GL-semantic: monitoring-metrics
 * @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * Monitoring and Metrics
 */

package monitoring

import (
	"log"
	"net/http"
	"sync"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	pipelineExecutions = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "esync_pipeline_executions_total",
			Help: "Total number of pipeline executions",
		},
		[]string{"pipeline_id", "status"},
	)
)

func init() {
	prometheus.MustRegister(pipelineExecutions)
}

// Monitor handles monitoring and metrics
type Monitor struct {
	mu     sync.RWMutex
	health bool
}

// NewMonitor creates a new monitor
func NewMonitor() *Monitor {
	return &Monitor{
		health: true,
	}
}

// Start starts the monitoring server
func (m *Monitor) Start(addr string) error {
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	mux.HandleFunc("/health", m.healthHandler)
	
	log.Printf("[Monitoring] Starting monitoring server on %s", addr)
	return http.ListenAndServe(addr, mux)
}

// healthHandler handles health check requests
func (m *Monitor) healthHandler(w http.ResponseWriter, r *http.Request) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.health {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("Unhealthy"))
	}
}

// RecordSuccess records a successful pipeline execution
func (m *Monitor) RecordSuccess(pipelineID string, recordCount int) {
	pipelineExecutions.WithLabelValues(pipelineID, "success").Inc()
}

// RecordError records a pipeline error
func (m *Monitor) RecordError(pipelineID, errorType string, err error) {
	pipelineExecutions.WithLabelValues(pipelineID, "error").Inc()
	log.Printf("[Monitoring] Error in pipeline %s [%s]: %v", pipelineID, errorType, err)
}

// RecordSourceError records a source connector error
func (m *Monitor) RecordSourceError(pipelineID string, err error) {
	pipelineExecutions.WithLabelValues(pipelineID, "source_error").Inc()
	log.Printf("[Monitoring] Source error in pipeline %s: %v", pipelineID, err)
}
