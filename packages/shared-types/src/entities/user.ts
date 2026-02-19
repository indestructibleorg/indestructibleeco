export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  role: "admin" | "member" | "viewer";
  metadata: Record<string, unknown>;
  last_sign_in_at: string | null;
  createdAt: string;
  updatedAt: string;
}
