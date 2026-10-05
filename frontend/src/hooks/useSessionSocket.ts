import { useEffect, useRef, useState } from "react";
import { sessionWebSocketUrl } from "../services/api";
import type { SessionSnapshot } from "../types";

export function useSessionSocket(sessionId: string | null, onUpdate: (snapshot: SessionSnapshot) => void) {
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "disconnected" | "error">("idle");
  const callbackRef = useRef(onUpdate);
  callbackRef.current = onUpdate;

  useEffect(() => {
    if (!sessionId) {
      setStatus("idle");
      return;
    }
    let closedByEffect = false;
    setStatus("connecting");
    const socket = new WebSocket(sessionWebSocketUrl(sessionId));
    socket.onopen = () => setStatus("connected");
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as SessionSnapshot | { type: string; message: string };
      if (payload.type === "session_update") callbackRef.current(payload as SessionSnapshot);
      if (payload.type === "error") setStatus("error");
    };
    socket.onerror = () => setStatus("error");
    socket.onclose = () => {
      if (!closedByEffect) setStatus("disconnected");
    };
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send("ping");
    }, 20_000);
    return () => {
      closedByEffect = true;
      window.clearInterval(heartbeat);
      socket.close();
    };
  }, [sessionId]);

  return status;
}
