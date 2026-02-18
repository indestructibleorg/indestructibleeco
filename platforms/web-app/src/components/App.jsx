import { useState } from "react";

const NODES = {
  core: { id: "core", label: "⚙️ Governance Engine", layer: "core", x: 500, y: 300, color: "#00f5d4", desc: "中樞治理引擎。協調所有子系統，執行 Schema 驗證、YAML 組裝與元數據填寫的全流程調度。" },
  cli: { id: "cli", label: "🖥️ CLI Interface", layer: "input", x: 100, y: 100, color: "#f72585", desc: "命令列入口。支援 yaml-gen <module.json>、yaml-validate、yaml-deploy 等指令，連接至治理引擎。" },
  nlp: { id: "nlp", label: "💬 NL Prompt", layer: "input", x: 100, y: 230, color: "#f72585", desc: "AI 自然語言提示器。使用 auto-generator-prompt.md 驅動，將模組描述轉換為結構化輸入。" },
  json_input: { id: "json_input", label: "📋 JSON Descriptor", layer: "input", x: 100, y: 360, color: "#f72585", desc: "標準化 JSON 輸入格式，定義 name, image, replicas, ports, depends_on 等模組屬性。" },
  schema_def: { id: "schema_def", label: "📐 Schema Definition", layer: "input", x: 100, y: 490, color: "#f72585", desc: "JSON Schema 檔案（schemas/ 目錄）。定義每種部署目標的必要欄位與驗證規則。" },
  meta_filler: { id: "meta_filler", label: "🏷️ Metadata Filler", layer: "process", x: 350, y: 130, color: "#7b2d8b", desc: "自動填寫 document_metadata：生成 unique_id（UUID v1）、target_system、cross_layer_binding 等欄位。" },
  template_engine: { id: "template_engine", label: "📝 Template Engine", layer: "process", x: 650, y: 130, color: "#7b2d8b", desc: "載入 templates/ 中的 .qyaml 基礎模板，注入變數，組裝最終 YAML 結構。" },
  vector_svc: { id: "vector_svc", label: "🧲 Vector Alignment", layer: "process", x: 350, y: 470, color: "#7b2d8b", desc: "使用 quantum-bert-xxl-v1（dim: 1024~4096）計算 vector_alignment_map，推斷服務依賴拓撲。" },
  registry_binder: { id: "registry_binder", label: "🔗 Registry Binder", layer: "process", x: 650, y: 470, color: "#7b2d8b", desc: "生成 registry_binding，將服務自動注冊到 Consul / Eureka 等服務發現系統。" },
  gov_meta: { id: "gov_meta", label: "📦 document_metadata", layer: "governance", x: 500, y: 480, color: "#4361ee", desc: "核心治理欄位：unique_id、target_system、cross_layer_binding、generated_by、schema_version。" },
  gov_info: { id: "gov_info", label: "🛡️ governance_info", layer: "governance", x: 280, y: 300, color: "#4361ee", desc: "策略與合規資訊：owner、approval_chain、compliance_tags、lifecycle_policy。" },
  reg_binding: { id: "reg_binding", label: "📡 registry_binding", layer: "governance", x: 720, y: 300, color: "#4361ee", desc: "服務目錄綁定：service_endpoint、discovery_protocol、health_check_path、registry_ttl。" },
  vec_map: { id: "vec_map", label: "🧬 vector_alignment", layer: "governance", x: 500, y: 120, color: "#4361ee", desc: "向量對齊映射：coherence_vector、function_keyword、contextual_binding。" },
  k8s: { id: "k8s", label: "☸️ K8s Deployment", layer: "output", x: 900, y: 100, color: "#06d6a0", desc: "輸出 Kubernetes Deployment / Service / ConfigMap YAML。相容 GKE。" },
  docker: { id: "docker", label: "🐋 Docker Compose", layer: "output", x: 900, y: 230, color: "#06d6a0", desc: "輸出 docker-compose.yml，包含服務依賴、埠映射、環境變數。" },
  helm: { id: "helm", label: "⛵ Helm Values", layer: "output", x: 900, y: 360, color: "#06d6a0", desc: "輸出 Helm Chart values.yaml，支援 subchart 依賴、環境覆蓋。" },
  nomad: { id: "nomad", label: "🏕️ Nomad Job", layer: "output", x: 900, y: 490, color: "#06d6a0", desc: "輸出 HashiCorp Nomad job spec，支援 task driver、資源限制。" },
  validator: { id: "validator", label: "✅ Schema Validator", layer: "validate", x: 500, y: 600, color: "#ffb703", desc: "多層驗證：欄位完整性、YAML 格式合規、id 結構、向量維度範圍、GKE 相容性。" },
  inference: { id: "inference", label: "🧠 Inference Router", layer: "core", x: 500, y: 190, color: "#00f5d4", desc: "多引擎推論路由：vLLM、TGI、SGLang、Ollama、TensorRT-LLM、LMDeploy、DeepSpeed。負載均衡與故障轉移。" },
  folding: { id: "folding", label: "🔄 Folding Engine", layer: "process", x: 200, y: 300, color: "#7b2d8b", desc: "程式碼折疊引擎：向量化折疊、圖結構折疊、混合折疊、實時索引更新。" },
  indexing: { id: "indexing", label: "🗂️ Index Engine", layer: "process", x: 800, y: 470, color: "#7b2d8b", desc: "混合索引引擎：FAISS 向量索引、Neo4j 圖索引、Elasticsearch 文本索引、混合路由。" },
};

const EDGES = [
  { from: "cli", to: "core" }, { from: "nlp", to: "core" }, { from: "json_input", to: "core" }, { from: "schema_def", to: "core" },
  { from: "core", to: "meta_filler" }, { from: "core", to: "template_engine" }, { from: "core", to: "vector_svc" }, { from: "core", to: "registry_binder" },
  { from: "meta_filler", to: "gov_meta" }, { from: "vector_svc", to: "vec_map" }, { from: "registry_binder", to: "reg_binding" }, { from: "core", to: "gov_info" },
  { from: "gov_meta", to: "core", dashed: true }, { from: "vec_map", to: "template_engine", dashed: true },
  { from: "core", to: "k8s" }, { from: "core", to: "docker" }, { from: "core", to: "helm" }, { from: "core", to: "nomad" },
  { from: "k8s", to: "validator" }, { from: "docker", to: "validator" }, { from: "helm", to: "validator" }, { from: "nomad", to: "validator" },
  { from: "validator", to: "core", dashed: true },
  { from: "core", to: "inference" }, { from: "inference", to: "core", dashed: true },
  { from: "core", to: "folding" }, { from: "folding", to: "indexing" }, { from: "indexing", to: "core", dashed: true },
];

const LAYER_META = {
  input: { label: "Input Layer", bg: "rgba(247,37,133,0.07)", border: "#f72585" },
  process: { label: "Processing Layer", bg: "rgba(123,45,139,0.08)", border: "#7b2d8b" },
  core: { label: "Core Engine", bg: "rgba(0,245,212,0.07)", border: "#00f5d4" },
  governance: { label: "Governance Block", bg: "rgba(67,97,238,0.09)", border: "#4361ee" },
  output: { label: "Output / Deploy", bg: "rgba(6,214,160,0.07)", border: "#06d6a0" },
  validate: { label: "Validation Layer", bg: "rgba(255,183,3,0.07)", border: "#ffb703" },
};

function LayerBadge({ layer }) {
  const m = LAYER_META[layer];
  return (
    <span style={{ fontSize: 9, fontFamily: "monospace", padding: "2px 6px", borderRadius: 3, border: `1px solid ${m.border}`, color: m.border, background: m.bg, letterSpacing: 1 }}>
      {m.label.toUpperCase()}
    </span>
  );
}

function ConceptNode({ node, selected, onClick }) {
  const col = node.color;
  const isSel = selected === node.id;
  return (
    <g transform={`translate(${node.x},${node.y})`} onClick={() => onClick(node.id)} style={{ cursor: "pointer" }}>
      <rect x={-72} y={-22} width={144} height={44} rx={8} fill={isSel ? col + "22" : "#0a0a14"} stroke={col} strokeWidth={isSel ? 2.5 : 1.2} style={{ filter: isSel ? `drop-shadow(0 0 8px ${col})` : `drop-shadow(0 0 3px ${col}44)` }} />
      <text textAnchor="middle" y={5} fill={col} fontSize={10} fontFamily="'Courier New', monospace" fontWeight="600">{node.label}</text>
    </g>
  );
}

function Arrow({ from, to, dashed }) {
  const a = NODES[from], b = NODES[to];
  if (!a || !b) return null;
  const dx = b.x - a.x, dy = b.y - a.y, len = Math.sqrt(dx * dx + dy * dy) || 1;
  const nx = dx / len, ny = dy / len;
  const sx = a.x + nx * 74, sy = a.y + ny * 22, ex = b.x - nx * 74, ey = b.y - ny * 22;
  const mx = (sx + ex) / 2, my = (sy + ey) / 2;
  const cx = mx - ny * 25, cy = my + nx * 25;
  return <path d={`M${sx},${sy} Q${cx},${cy} ${ex},${ey}`} fill="none" stroke={dashed ? "#ffffff20" : "#ffffff15"} strokeWidth={dashed ? 1 : 1.2} strokeDasharray={dashed ? "5,4" : "none"} markerEnd="url(#arrow)" />;
}

export default function App() {
  const [selected, setSelected] = useState("core");
  const [activeLayer, setActiveLayer] = useState(null);
  const node = NODES[selected];
  const handleClick = (id) => setSelected(id === selected ? null : id);

  return (
    <div style={{ minHeight: "100vh", background: "#06060f", fontFamily: "'Courier New', monospace", color: "#e0e0e0", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "18px 32px 0", borderBottom: "1px solid #ffffff10", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 10, color: "#4361ee", letterSpacing: 4, marginBottom: 4 }}>ARCHITECTURE CONCEPT MAP · v1.0</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#ffffff", letterSpacing: 2 }}>indestructibleeco</div>
          <div style={{ fontSize: 11, color: "#ffffff50", marginTop: 2, marginBottom: 14 }}>YAML Governance & AI Inference Framework</div>
        </div>
        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {Object.entries(LAYER_META).map(([key, m]) => (
            <button key={key} onClick={() => setActiveLayer(activeLayer === key ? null : key)} style={{ fontSize: 9, padding: "3px 10px", borderRadius: 20, border: `1px solid ${m.border}`, color: activeLayer === key ? "#000" : m.border, background: activeLayer === key ? m.border : "transparent", cursor: "pointer", letterSpacing: 1, transition: "all .15s" }}>
              {m.label}
            </button>
          ))}
          {activeLayer && <button onClick={() => setActiveLayer(null)} style={{ fontSize: 9, padding: "3px 10px", borderRadius: 20, border: "1px solid #ffffff40", color: "#fff", background: "transparent", cursor: "pointer" }}>✕ Clear</button>}
        </div>
      </div>
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "auto" }}>
          <svg width={1060} height={680} style={{ display: "block", minWidth: "100%" }}>
            <defs>
              <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="#ffffff25" /></marker>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#ffffff05" strokeWidth="0.5" /></pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            {EDGES.map((e, i) => <Arrow key={i} from={e.from} to={e.to} dashed={e.dashed} />)}
            {activeLayer && (() => {
              const ln = Object.values(NODES).filter(n => n.layer === activeLayer);
              if (!ln.length) return null;
              const xs = ln.map(n => n.x), ys = ln.map(n => n.y), pad = 60;
              const m = LAYER_META[activeLayer];
              return <rect x={Math.min(...xs) - pad} y={Math.min(...ys) - pad} width={Math.max(...xs) - Math.min(...xs) + pad * 2 + 40} height={Math.max(...ys) - Math.min(...ys) + pad * 2 + 20} rx={12} fill={m.bg} stroke={m.border} strokeWidth={1} strokeDasharray="6,4" opacity={0.8} />;
            })()}
            {selected && EDGES.filter(e => e.from === selected || e.to === selected).map((e, i) => {
              const a = NODES[e.from], b = NODES[e.to];
              return a && b ? <line key={"hl" + i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={NODES[selected].color + "60"} strokeWidth={2} /> : null;
            })}
            {Object.values(NODES).filter(n => !activeLayer || n.layer === activeLayer).map(n => <ConceptNode key={n.id} node={n} selected={selected} onClick={handleClick} />)}
          </svg>
        </div>
        <div style={{ width: 300, background: "#0d0d1a", borderLeft: "1px solid #ffffff0f", padding: 24, display: "flex", flexDirection: "column", overflowY: "auto" }}>
          {node ? (<>
            <div style={{ marginBottom: 16 }}><LayerBadge layer={node.layer} /></div>
            <div style={{ fontSize: 16, fontWeight: 700, color: node.color, marginBottom: 12, lineHeight: 1.4, textShadow: `0 0 12px ${node.color}66` }}>{node.label}</div>
            <div style={{ fontSize: 12, color: "#c0c0d0", lineHeight: 1.8, marginBottom: 20, borderLeft: `2px solid ${node.color}44`, paddingLeft: 12 }}>{node.desc}</div>
            <div style={{ fontSize: 10, color: "#ffffff40", marginBottom: 8, letterSpacing: 2 }}>CONNECTIONS</div>
            {EDGES.filter(e => e.from === node.id || e.to === node.id).map((e, i) => {
              const other = e.from === node.id ? NODES[e.to] : NODES[e.from];
              const dir = e.from === node.id ? "→" : "←";
              return other ? (
                <div key={i} onClick={() => setSelected(other.id)} style={{ padding: "6px 10px", marginBottom: 4, background: "#ffffff06", borderRadius: 6, fontSize: 11, color: other.color, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, border: `1px solid ${other.color}22` }}>
                  <span style={{ color: "#ffffff30" }}>{dir}</span>{other.label}{e.dashed && <span style={{ color: "#ffffff20", fontSize: 9 }}>feedback</span>}
                </div>
              ) : null;
            })}
          </>) : <div style={{ color: "#ffffff30", fontSize: 12, marginTop: 40, textAlign: "center" }}>Click any node to explore.</div>}
          <div style={{ marginTop: "auto", paddingTop: 24, borderTop: "1px solid #ffffff0a" }}>
            <div style={{ fontSize: 9, color: "#ffffff30", letterSpacing: 2, marginBottom: 10 }}>SYSTEM METRICS</div>
            {[["Nodes", Object.keys(NODES).length], ["Connections", EDGES.length], ["Layers", Object.keys(LAYER_META).length], ["Output Targets", 4], ["Inference Engines", 7], ["Index Backends", 3]].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#ffffff50", marginBottom: 5 }}><span>{k}</span><span style={{ color: "#00f5d4" }}>{v}</span></div>
            ))}
          </div>
        </div>
      </div>
      <div style={{ padding: "8px 32px", borderTop: "1px solid #ffffff08", display: "flex", gap: 32, fontSize: 9, color: "#ffffff25", letterSpacing: 1 }}>
        <span>VERSION · v1.0.0</span><span>FORMAT · .qyaml</span><span>VECTOR · quantum-bert-xxl-v1</span><span>DIM · 1024~4096</span><span>ENGINES · vLLM/TGI/SGLang/Ollama/TRT-LLM/LMDeploy/DeepSpeed</span>
      </div>
    </div>
  );
}