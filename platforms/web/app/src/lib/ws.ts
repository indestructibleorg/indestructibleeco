const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:3000/ws";

type Handler = (data: unknown) => void;

class WS {
  private socket: WebSocket | null = null;
  private handlers = new Map<string, Set<Handler>>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private attempts = 0;

  connect(token?: string): void {
    const url = token ? `${WS_URL}?token=${encodeURIComponent(token)}` : WS_URL;
    this.socket = new WebSocket(url);
    this.socket.onopen = () => { this.attempts = 0; this.emit("connected", {}); };
    this.socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        this.emit(msg.type || "message", msg.data || msg);
      } catch { this.emit("message", e.data); }
    };
    this.socket.onclose = () => {
      this.emit("disconnected", {});
      if (this.attempts < 10) {
        this.reconnectTimer = setTimeout(() => { this.attempts++; this.connect(token); }, 3000 * Math.pow(1.5, this.attempts));
      }
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.socket?.close(1000);
    this.socket = null;
  }

  send(type: string, data: unknown): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, data }));
    }
  }

  on(event: string, handler: Handler): () => void {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  private emit(event: string, data: unknown): void {
    this.handlers.get(event)?.forEach((h) => { try { h(data); } catch {} });
  }
}

export const ws = new WS();
