export function normalize(channel: "whatsapp" | "telegram" | "line" | "messenger", raw: unknown) {
  return { channel, userId: "unknown", text: "", intent: null, raw, ts: Date.now() };
}
