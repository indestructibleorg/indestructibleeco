export interface NormalizedMessage { channel: "whatsapp" | "telegram" | "line" | "messenger"; userId: string; text: string; intent: string | null; raw: unknown; ts: number; }
