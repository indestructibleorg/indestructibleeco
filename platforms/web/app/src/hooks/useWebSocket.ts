import { useEffect, useRef, useCallback } from "react";
import { ws } from "../lib/ws";
import { useAuthStore } from "../store/auth";

export function useWebSocket() {
  const token = useAuthStore((s) => s.token);
  const connected = useRef(false);

  useEffect(() => {
    if (token && !connected.current) {
      ws.connect(token);
      connected.current = true;
    }
    return () => {
      if (connected.current) {
        ws.disconnect();
        connected.current = false;
      }
    };
  }, [token]);

  const subscribe = useCallback((event: string, handler: (data: unknown) => void) => {
    return ws.on(event, handler);
  }, []);

  const send = useCallback((type: string, data: unknown) => {
    ws.send(type, data);
  }, []);

  return { subscribe, send };
}
