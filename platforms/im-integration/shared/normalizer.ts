/**
 * Message Normalizer — unified message format across all IM channels.
 *
 * Converts channel-specific payloads into a common IndestructibleEco
 * message format for routing, session management, and AI processing.
 */

export type Channel = "whatsapp" | "telegram" | "line" | "messenger";

export interface NormalizedMessage {
  id: string;
  channel: Channel;
  userId: string;
  userName: string;
  text: string;
  timestamp: string;
  replyTo: string | null;
  metadata: Record<string, unknown>;
  uri: string;
  urn: string;
}

export interface OutboundMessage {
  channel: Channel;
  userId: string;
  text: string;
  metadata?: Record<string, unknown>;
}

export function normalizeWhatsApp(payload: Record<string, any>): NormalizedMessage {
  const entry = payload.entry?.[0];
  const change = entry?.changes?.[0]?.value;
  const msg = change?.messages?.[0];
  const contact = change?.contacts?.[0];
  const id = msg?.id || crypto.randomUUID();

  return {
    id,
    channel: "whatsapp",
    userId: msg?.from || "",
    userName: contact?.profile?.name || "",
    text: msg?.text?.body || "",
    timestamp: new Date(parseInt(msg?.timestamp || "0") * 1000).toISOString(),
    replyTo: msg?.context?.id || null,
    metadata: { messageType: msg?.type, phoneNumberId: change?.metadata?.phone_number_id },
    uri: `indestructibleeco://im/whatsapp/message/${id}`,
    urn: `urn:indestructibleeco:im:whatsapp:message:${msg?.from}:${id}`,
  };
}

export function normalizeTelegram(payload: Record<string, any>): NormalizedMessage {
  const msg = payload.message || payload.edited_message;
  const id = String(msg?.message_id || crypto.randomUUID());

  return {
    id,
    channel: "telegram",
    userId: String(msg?.from?.id || ""),
    userName: [msg?.from?.first_name, msg?.from?.last_name].filter(Boolean).join(" "),
    text: msg?.text || "",
    timestamp: new Date((msg?.date || 0) * 1000).toISOString(),
    replyTo: msg?.reply_to_message ? String(msg.reply_to_message.message_id) : null,
    metadata: { chatId: msg?.chat?.id, chatType: msg?.chat?.type },
    uri: `indestructibleeco://im/telegram/message/${id}`,
    urn: `urn:indestructibleeco:im:telegram:message:${msg?.from?.id}:${id}`,
  };
}

export function normalizeLINE(payload: Record<string, any>): NormalizedMessage {
  const event = payload.events?.[0];
  const id = event?.message?.id || crypto.randomUUID();

  return {
    id,
    channel: "line",
    userId: event?.source?.userId || "",
    userName: "",
    text: event?.message?.text || "",
    timestamp: new Date(event?.timestamp || 0).toISOString(),
    replyTo: null,
    metadata: { replyToken: event?.replyToken, sourceType: event?.source?.type },
    uri: `indestructibleeco://im/line/message/${id}`,
    urn: `urn:indestructibleeco:im:line:message:${event?.source?.userId}:${id}`,
  };
}

export function normalizeMessenger(payload: Record<string, any>): NormalizedMessage {
  const entry = payload.entry?.[0];
  const messaging = entry?.messaging?.[0];
  const msg = messaging?.message;
  const id = msg?.mid || crypto.randomUUID();

  return {
    id,
    channel: "messenger",
    userId: messaging?.sender?.id || "",
    userName: "",
    text: msg?.text || "",
    timestamp: new Date(messaging?.timestamp || 0).toISOString(),
    replyTo: msg?.reply_to?.mid || null,
    metadata: { pageId: entry?.id },
    uri: `indestructibleeco://im/messenger/message/${id}`,
    urn: `urn:indestructibleeco:im:messenger:message:${messaging?.sender?.id}:${id}`,
  };
}

export function normalize(channel: Channel, payload: Record<string, any>): NormalizedMessage {
  switch (channel) {
    case "whatsapp": return normalizeWhatsApp(payload);
    case "telegram": return normalizeTelegram(payload);
    case "line": return normalizeLINE(payload);
    case "messenger": return normalizeMessenger(payload);
  }
}