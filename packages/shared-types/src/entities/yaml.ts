export interface QyamlDocumentMetadata { unique_id: string; target_system: string; cross_layer_binding: string[]; schema_version: string; generated_by: string; created_at: string; }
export interface QyamlGovernanceInfo { owner: string; approval_chain: string[]; compliance_tags: string[]; lifecycle_policy: string; }
export interface QyamlRegistryBinding { service_endpoint: string; discovery_protocol: "consul" | "etcd" | "eureka"; health_check_path: string; registry_ttl: number; }
export interface QyamlVectorAlignmentMap { alignment_model: "quantum-bert-xxl-v1"; coherence_vector: number[]; function_keyword: string[]; contextual_binding: string; }
export interface QyamlDocument { document_metadata: QyamlDocumentMetadata; governance_info: QyamlGovernanceInfo; registry_binding: QyamlRegistryBinding; vector_alignment_map: QyamlVectorAlignmentMap; }
export interface ModuleDescriptor { name: string; image?: string; replicas?: number; ports?: number[]; depends_on?: string[]; labels?: Record<string, string>; env?: Record<string, string>; }
