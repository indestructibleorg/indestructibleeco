import type { ModuleDescriptor } from "../entities/yaml";
export interface LoginRequest { email: string; password: string }
export interface YamlGenRequest { module: ModuleDescriptor; target: "k8s" | "docker" | "helm" | "nomad" }
export interface AiGenRequest { prompt: string; model_id?: string; params?: Record<string, string> }
