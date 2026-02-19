export interface Platform {
  id: string;
  name: string;
  slug: string;
  type: "web" | "desktop" | "im" | "extension" | "custom";
  status: "active" | "inactive" | "deploying";
  capabilities: string[];
  config: Record<string, unknown>;
  ownerId: string;
  k8sNamespace: string;
  uri: string;
  urn: string;
  createdAt: string;
  updatedAt: string;
}
