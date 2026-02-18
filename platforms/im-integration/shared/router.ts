/**
 * Message Router — routes normalized messages to AI backend and manages sessions.
 *
 * Redis-backed conversation state per user/channel.
 */

import Redis from "ioredis";
import pino from "pino";
import type { NormalizedMessage, OutboundMessage, Channel } from "./normalizer";

const logger = pino({ level: process.env.LOG_LEVEL || "info" });

interface SessionState {
  userId: string;
  channel: Channel;
  conversationId: string;
  messageCount: number;
  lastMessageAt: string;
  context: Record<string, unknown>;
}

export class MessageRouter {
  private redis: Redis;
  private sessionTTL: number;

  constructor(redisUrl: string = process.env.REDIS_URL || "redis://localhost:6379", sessionTTL = 3600) {
    this.redis = new Redis(redisUrl, { maxRetriesPerRequest: 3, lazyConnect: true });
    this.sessionTTL = sessionTTL;
  }

  async route(message: NormalizedMessage): Promise<OutboundMessage> {
    const session = await this.getOrCreateSession(message);

    logger.info({
      msg: "Routing message",
      channel: message.channel,
      userId: message.userId,
      conversationId: session.conversationId,
      messageCount: session.messageCount,
    });

    // Forward to AI backend
    const aiResponse = await this.forwardToAI(message, session);

    // Update session
    session.messageCount++;
    session.lastMessageAt = new Date().toISOString();
    await this.saveSession(session);

    return {
      channel: message.channel,
      userId: message.userId,
      text: aiResponse,
      metadata: { conversationId: session.conversationId },
    };
  }

  private async getOrCreateSession(message: NormalizedMessage): Promise<SessionState> {
    const key = `session:${message.channel}:${message.userId}`;
    const existing = await this.redis.get(key);

    if (existing) {
      return JSON.parse(existing);
    }

    const session: SessionState = {
      userId: message.userId,
      channel: message.channel,
      conversationId: crypto.randomUUID(),
      messageCount: 0,
      lastMessageAt: new Date().toISOString(),
      context: {},
    };

    await this.saveSession(session);
    return session;
  }

  private async saveSession(session: SessionState): Promise<void> {
    const key = `session:${session.channel}:${session.userId}`;
    await this.redis.setex(key, this.sessionTTL, JSON.stringify(session));
  }

  private async forwardToAI(message: NormalizedMessage, session: SessionState): Promise<string> {
    const apiUrl = process.env.API_URL || "http://localhost:3000";

    try {
      const res = await fetch(`${apiUrl}/api/v1/ai/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${process.env.SERVICE_TOKEN || ""}`,
        },
        body: JSON.stringify({
          prompt: message.text,
          model_id: "default",
          params: {
            channel: message.channel,
            conversationId: session.conversationId,
            userId: message.userId,
          },
        }),
        signal: AbortSignal.timeout(30000),
      });

      if (res.ok) {
        const data = await res.json();
        return data.result || data.content || "Processing your request...";
      }

      logger.warn({ status: res.status, msg: "AI service returned non-OK" });
      return "I'm having trouble processing your request. Please try again.";
    } catch (err) {
      logger.error({ err: (err as Error).message, msg: "Failed to reach AI service" });
      return "Service temporarily unavailable. Please try again later.";
    }
  }

  async destroy(): Promise<void> {
    await this.redis.quit();
  }
}