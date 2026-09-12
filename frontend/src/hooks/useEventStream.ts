/**
 * Live event subscription over the NexusOps WebSocket hub.
 *
 * - Authenticates with the in-memory access token on connect.
 * - Reconnects with capped exponential backoff (1s → 15s).
 * - Re-authenticates + resubscribes automatically after reconnects.
 */

import { useEffect, useRef } from "react";
import { getAccessToken, refreshToken } from "../api/client";

export type WsChannel =
  | "global"
  | "server-metrics"
  | "container-logs"
  | "deployment-logs"
  | "incidents";

export interface WsFrame {
  type: string;
  channel?: string;
  params?: Record<string, string>;
  data?: Record<string, unknown>;
  code?: string;
}

interface Subscription {
  channel: WsChannel;
  params: Record<string, string>;
  handler: (frame: WsFrame) => void;
}

const WS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/v1/ws`;

export function useEventStream(
  subscriptions: Array<{ channel: WsChannel; params?: Record<string, string> }>,
  onFrame: (frame: WsFrame) => void,
): void {
  const subsRef = useRef<Subscription[]>([]);
  const handlerRef = useRef(onFrame);
  handlerRef.current = onFrame;

  // Stable JSON signature so effect re-runs only when the subscription set changes.
  const signature = JSON.stringify(subscriptions);
  useEffect(() => {
    subsRef.current = (JSON.parse(signature) as Array<{ channel: WsChannel; params?: Record<string, string> }>).map(
      (s) => ({ channel: s.channel, params: s.params ?? {}, handler: (f: WsFrame) => handlerRef.current(f) }),
    );
  }, [signature]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closed = false;
    let attempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const send = (payload: Record<string, unknown>) => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
    };

    const subscribeAll = () => {
      for (const sub of subsRef.current) {
        // The hub reads channel parameters from the nested "params" dict
        // (Hub._subscribe: message.get("params")) — an empty object is fine
        // for the unparameterized channels (global, incidents).
        send({ action: "subscribe", channel: sub.channel, params: sub.params });
      }
    };

    const dispatch = (frame: WsFrame) => {
      if (frame.type === "event" || frame.type === "error" || frame.type === "notify") {
        for (const sub of subsRef.current) {
          if (frame.channel && frame.channel !== sub.channel) continue;
          const paramKeys = Object.keys(sub.params);
          if (paramKeys.some((k) => frame.params?.[k] !== undefined && frame.params[k] !== sub.params[k])) {
            continue;
          }
          sub.handler(frame);
        }
      }
    };

    const connect = () => {
      if (closed) return;
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        attempt = 0;
        // The hub never acks with an "auth_ok" frame — after a valid auth
        // frame it simply starts serving, so subscribe immediately after
        // issuing auth (frames are processed in order, and subscribing on
        // every open also covers reconnects).
        const authenticate = () => {
          const token = getAccessToken();
          if (!token) return false;
          send({ action: "auth", token });
          subscribeAll();
          return true;
        };
        if (authenticate()) return;
        // No token yet (e.g. page reloaded); renew silently then auth + subscribe.
        void refreshToken().then((ok) => {
          if (!ok) return;
          authenticate();
        });
      };

      socket.onmessage = (message) => {
        try {
          dispatch(JSON.parse(message.data as string) as WsFrame);
        } catch {
          // Ignore malformed frames — the server is trusted but be defensive.
        }
      };

      socket.onclose = () => {
        if (closed) return;
        attempt += 1;
        const delay = Math.min(1000 * 2 ** Math.min(attempt, 4), 15000);
        reconnectTimer = setTimeout(connect, delay);
      };

      socket.onerror = () => socket?.close();
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
    // Re-establish the whole connection (with fresh auth) whenever the
    // subscription set changes or a new access token lands.
  }, [signature]);
}
