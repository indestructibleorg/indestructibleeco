// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: esync-platform-source
// @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
//
// GL Unified Charter Activated
/**
 * @GL-governed
 * @GL-layer: esync-platform
 * @GL-semantic: connector-interface
 * @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * Connector Interface - Multi-Source Sync Platform
 */

package connectors

import (
	"context"
	"time"
)

// Record represents a data record
type Record struct {
	ID        string                 `json:"id"`
	Operation string                 `json:"operation"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
}

// Checkpoint marks sync progress
type Checkpoint struct {
	Position string                 `json:"position"`
	Metadata map[string]interface{} `json:"metadata"`
}

// ValidationResult holds validation results
type ValidationResult struct {
	IsValid bool     `json:"is_valid"`
	Errors  []string `json:"errors"`
}

// Connector is the base interface for all source and target connectors
type Connector interface {
	ListChanges(ctx context.Context, checkpoint *Checkpoint) ([]Record, error)
	ApplyChanges(ctx context.Context, changes []Record) error
	Validate(ctx context.Context, record Record) ValidationResult
	ResolveConflict(ctx context.Context, existing Record, newSource Record) (Record, error)
	GetLatestCheckpoint(ctx context.Context) (*Checkpoint, error)
}
