/**
 * YAMLStudio — .qyaml editor + validation + generation
 * URI: indestructibleeco://platforms/web/pages/YAMLStudio
 */
import { useState, useCallback } from 'react';

interface ValidationError {
  path: string;
  message: string;
  severity: 'error' | 'warning';
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

const DEFAULT_TEMPLATE = `# IndestructibleEco .qyaml Template
document_metadata:
  unique_id: ""
  uri: "indestructibleeco://"
  urn: "urn:indestructibleeco:"
  target_system: "gke-production"
  schema_version: "v1"
  generated_by: "yaml-studio"
  created_at: ""

governance_info:
  owner: "platform-team"
  compliance_tags:
    - zero-trust
    - soc2
  lifecycle_policy: "active"

registry_binding:
  service_endpoint: ""
  health_check_path: "/health"

vector_alignment_map:
  alignment_model: "quantum-bert-xxl-v1"
  coherence_vector_dim: 1024
`;

export default function YAMLStudio() {
  const [content, setContent] = useState(DEFAULT_TEMPLATE);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [generating, setGenerating] = useState(false);
  const [serviceName, setServiceName] = useState('');
  const [namespace, setNamespace] = useState('indestructibleeco');
  const [kind, setKind] = useState('Deployment');

  const handleValidate = useCallback(async () => {
    try {
      const resp = await fetch('/api/v1/yaml/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      const data = await resp.json();
      setValidation(data);
    } catch {
      setValidation({ valid: false, errors: [{ path: '/', message: 'Validation request failed', severity: 'error' }] });
    }
  }, [content]);

  const handleGenerate = useCallback(async () => {
    if (!serviceName) return;
    setGenerating(true);
    try {
      const resp = await fetch('/api/v1/yaml/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: serviceName, namespace, kind }),
      });
      const data = await resp.json();
      if (data.content) setContent(data.content);
      else if (data.yaml) setContent(data.yaml);
    } catch {
      // silent
    } finally {
      setGenerating(false);
    }
  }, [serviceName, namespace, kind]);

  return (
    <div className="yaml-studio">
      <div className="page-header">
        <h1>YAML Studio</h1>
        <p className="subtitle">.qyaml editor with governance validation</p>
      </div>

      <div className="studio-layout">
        <div className="generator-panel">
          <h3>Generate .qyaml</h3>
          <div className="form-group">
            <label>Service Name</label>
            <input
              type="text"
              value={serviceName}
              onChange={(e) => setServiceName(e.target.value)}
              placeholder="eco-my-service"
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Namespace</label>
            <input
              type="text"
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Kind</label>
            <select value={kind} onChange={(e) => setKind(e.target.value)} className="input">
              <option value="Deployment">Deployment</option>
              <option value="Service">Service</option>
              <option value="Ingress">Ingress</option>
              <option value="ConfigMap">ConfigMap</option>
            </select>
          </div>
          <button onClick={handleGenerate} disabled={generating || !serviceName} className="btn btn-primary">
            {generating ? 'Generating...' : 'Generate'}
          </button>
        </div>

        <div className="editor-panel">
          <div className="editor-toolbar">
            <button onClick={handleValidate} className="btn btn-secondary">Validate</button>
            <button onClick={() => setContent(DEFAULT_TEMPLATE)} className="btn btn-ghost">Reset</button>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="yaml-editor"
            spellCheck={false}
          />
        </div>

        <div className="validation-panel">
          <h3>Validation Results</h3>
          {validation === null ? (
            <p className="text-muted">Click "Validate" to check your .qyaml</p>
          ) : validation.valid ? (
            <div className="validation-success">
              <span className="status-icon">\u2705</span> Valid .qyaml document
            </div>
          ) : (
            <div className="validation-errors">
              {validation.errors.map((err, i) => (
                <div key={i} className={`validation-error severity-${err.severity}`}>
                  <span className="error-path">{err.path}</span>
                  <span className="error-message">{err.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
