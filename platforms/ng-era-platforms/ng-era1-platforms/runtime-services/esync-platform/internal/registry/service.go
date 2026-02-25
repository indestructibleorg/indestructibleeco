// @GL-governed
// @GL-layer: GL10-29
// @GL-semantic: esync-platform-source
// @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
//
// GL Unified Charter Activated
/**
 * @GL-governed
 * @GL-layer: esync-platform
 * @GL-semantic: pipeline-registry-service
 * @GL-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * Pipeline Registry Service
 */

package registry

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"gopkg.in/yaml.v3"
)

// Pipeline represents a sync pipeline configuration
type Pipeline struct {
	ID          string                 `yaml:"id"`
	Version     string                 `yaml:"version"`
	Description string                 `yaml:"description"`
	GLMetadata  map[string]interface{} `yaml:",inline"`
}

// Service manages pipeline lifecycle
type Service struct {
	pipelines     map[string]*Pipeline
	mu            sync.RWMutex
	pipelinesDir  string
}

// NewService creates a new pipeline registry service
func NewService(pipelinesDir string) *Service {
	return &Service{
		pipelines:     make(map[string]*Pipeline),
		pipelinesDir:  pipelinesDir,
	}
}

// LoadAll loads all pipeline definitions from directory
func (s *Service) LoadAll(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	files, err := filepath.Glob(filepath.Join(s.pipelinesDir, "*.yaml"))
	if err != nil {
		return fmt.Errorf("failed to scan pipelines directory: %w", err)
	}

	for _, file := range files {
		pipeline, err := s.loadFromFile(file)
		if err != nil {
			return fmt.Errorf("failed to load pipeline from %s: %w", file, err)
		}
		s.pipelines[pipeline.ID] = pipeline
	}

	return nil
}

// loadFromFile loads a single pipeline from file
func (s *Service) loadFromFile(filepath string) (*Pipeline, error) {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var pipeline Pipeline
	if err := yaml.Unmarshal(data, &pipeline); err != nil {
		return nil, fmt.Errorf("failed to parse YAML: %w", err)
	}

	return &pipeline, nil
}

// GetByID returns a pipeline by ID
func (s *Service) GetByID(id string) (*Pipeline, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	pipeline, exists := s.pipelines[id]
	if !exists {
		return nil, fmt.Errorf("pipeline %s not found", id)
	}

	return pipeline, nil
}

// GetAll returns all pipelines
func (s *Service) GetAll() []*Pipeline {
	s.mu.RLock()
	defer s.mu.RUnlock()

	pipelines := make([]*Pipeline, 0, len(s.pipelines))
	for _, p := range s.pipelines {
		pipelines = append(pipelines, p)
	}

	return pipelines
}
