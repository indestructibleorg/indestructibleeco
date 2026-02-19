import { io, type Socket } from "socket.io-client";
export function createWsClient(url: string, token: string): Socket {
  return io(url, { auth: { token }, transports: ["websocket"], reconnectionAttempts: 5, reconnectionDelay: 2000 });
}
