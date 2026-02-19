export interface LoginResponse { access_token: string; expires_in: number }
export interface YamlGenResponse { qyaml_content: string; valid: boolean; warnings: string[] }
export interface AiGenResponse { job_id: string; status: "queued" }
