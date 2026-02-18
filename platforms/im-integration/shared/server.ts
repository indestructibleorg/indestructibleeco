/**
 * IM Integration Webhook Server — unified entry point for all channels.
 *
 * Each channel has its own webhook path validated with platform secrets.
 * Shared logic handles normalization, routing, and session management.
 */

import express from "express";
import pino from "pino";
import crypto from "crypto";
import { normalize, type Channel } from "./normalizer";
import { MessageRouter } from "./router";

const logger = pino({ level: process.env.LOG_LEVEL || "info" });
const app = express();
const router = new MessageRouter();

app.use(express.json());

// ─── Webhook Verification Helpers ───

function verifyWhatsAppSignature(req: express.Request): boolean {
  const signature = req.headers["x-hub-signature-256"] as string;
  if (!signature) return false;
  const secret = process.env.WHATSAPP_APP_SECRET || "";
  const hash = "sha256=" + crypto.createHmac("sha256", secret).update(JSON.stringify(req.body)).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(hash));
}

function verifyTelegramSecret(req: express.Request): boolean {
  const token = req.params.token;
  return token === process.env.TELEGRAM_BOT_TOKEN;
}

function verifyLINESignature(req: express.Request): boolean {
  const signature = req.headers["x-line-signature"] as string;
  if (!signature) return false;
  const secret = process.env.LINE_CHANNEL_SECRET || "";
  const hash = crypto.createHmac("sha256", secret).update(JSON.stringify(req.body)).digest("base64");
  return signature === hash;
}

function verifyMessengerSignature(req: express.Request): boolean {
  const signature = req.headers["x-hub-signature-256"] as string;
  if (!signature) return false;
  const secret = process.env.MESSENGER_APP_SECRET || "";
  const hash = "sha256=" + crypto.createHmac("sha256", secret).update(JSON.stringify(req.body)).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(hash));
}

// ─── Channel Webhook Handlers ───

async function handleWebhook(channel: Channel, req: express.Request, res: express.Response) {
  try {
    const message = normalize(channel, req.body);
    if (!message.text) {
      res.status(200).json({ status: "ignored", reason: "no_text" });
      return;
    }

    const response = await router.route(message);

    logger.info({
      msg: "Message processed",
      channel,
      userId: message.userId,
      uri: message.uri,
    });

    // Channel-specific response delivery would go here
    // (WhatsApp Cloud API, Telegram sendMessage, LINE reply, Messenger send)

    res.status(200).json({ status: "ok", responseText: response.text });
  } catch (err) {
    logger.error({ err: (err as Error).message, channel, msg: "Webhook processing failed" });
    res.status(500).json({ error: "processing_failed" });
  }
}

// ─── WhatsApp ───
app.get("/webhook/whatsapp", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  if (mode === "subscribe" && token === process.env.WHATSAPP_VERIFY_TOKEN) {
    res.status(200).send(challenge);
  } else {
    res.status(403).send("Forbidden");
  }
});

app.post("/webhook/whatsapp", (req, res) => {
  if (!verifyWhatsAppSignature(req)) {
    res.status(401).json({ error: "invalid_signature" });
    return;
  }
  handleWebhook("whatsapp", req, res);
});

// ─── Telegram ───
app.post("/webhook/telegram/:token", (req, res) => {
  if (!verifyTelegramSecret(req)) {
    res.status(401).json({ error: "invalid_token" });
    return;
  }
  handleWebhook("telegram", req, res);
});

// ─── LINE ───
app.post("/webhook/line", (req, res) => {
  if (!verifyLINESignature(req)) {
    res.status(401).json({ error: "invalid_signature" });
    return;
  }
  handleWebhook("line", req, res);
});

// ─── Messenger ───
app.get("/webhook/messenger", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  if (mode === "subscribe" && token === process.env.MESSENGER_VERIFY_TOKEN) {
    res.status(200).send(challenge);
  } else {
    res.status(403).send("Forbidden");
  }
});

app.post("/webhook/messenger", (req, res) => {
  if (!verifyMessengerSignature(req)) {
    res.status(401).json({ error: "invalid_signature" });
    return;
  }
  handleWebhook("messenger", req, res);
});

// ─── Health ───
app.get("/health", (_req, res) => {
  res.status(200).json({
    status: "healthy",
    service: "im-integration",
    version: "1.0.0",
    uri: "indestructibleeco://platform/im-integration/health",
    channels: ["whatsapp", "telegram", "line", "messenger"],
  });
});

// ─── Start ───
const port = parseInt(process.env.PORT || "4000", 10);
app.listen(port, () => {
  logger.info({ msg: "IM Integration server started", port, uri: "indestructibleeco://platform/im-integration" });
});

export { app };