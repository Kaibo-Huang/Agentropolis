import type {
  ArchetypeListResponse,
  AvatarParamsResponse,
  EventResponse,
  FollowerListResponse,
  FollowerResponse,
  InjectEventRequest,
  PostListResponse,
  SessionConfig,
  SessionResponse,
  TickRequest,
  TickResponse,
  WsIncoming,
  WsOutgoing,
} from "./types";

// ── Error type ──────────────────────────────────────────────────────────────

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    const message =
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof (body as { detail: unknown }).detail === "string"
        ? (body as { detail: string }).detail
        : `HTTP ${status}`;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ── REST client ─────────────────────────────────────────────────────────────

export class ApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    // Strip trailing slash for consistent path concatenation
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    };

    const response = await fetch(url, { ...init, headers });

    // 204 No Content — return undefined cast to T
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    // Parse body for both success and error paths
    let body: unknown;
    const contentType = response.headers.get("Content-Type") ?? "";
    if (contentType.includes("application/json")) {
      body = await response.json();
    } else {
      body = await response.text();
    }

    if (!response.ok) {
      throw new ApiError(response.status, body);
    }

    return body as T;
  }

  // ── Sessions ──

  createSession(config?: SessionConfig): Promise<SessionResponse> {
    const body = config ? { config } : {};
    return this.request<SessionResponse>("/api/sessions", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  getSession(sessionId: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(`/api/sessions/${sessionId}`);
  }

  deleteSession(sessionId: string): Promise<void> {
    return this.request<void>(`/api/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  resumeSession(sessionId: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(
      `/api/sessions/${sessionId}/resume`,
      { method: "POST" },
    );
  }

  pauseSession(sessionId: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(
      `/api/sessions/${sessionId}/pause`,
      { method: "POST" },
    );
  }

  // ── Tick ──

  tick(sessionId: string, body: TickRequest): Promise<TickResponse> {
    return this.request<TickResponse>(`/api/sessions/${sessionId}/tick`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  // ── Followers ──

  getFollowers(
    sessionId: string,
    offset = 0,
    limit = 1000,
  ): Promise<FollowerListResponse> {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    return this.request<FollowerListResponse>(
      `/api/sessions/${sessionId}/followers?${params}`,
    );
  }

  /** Create a follower with a custom avatar (e.g. user joining the simulation). */
  createFollower(
    sessionId: string,
    body: { name: string; avatar_params: AvatarParamsResponse; volatility?: number },
  ): Promise<FollowerResponse> {
    return this.request<FollowerResponse>(
      `/api/sessions/${sessionId}/followers`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  }

  // ── Archetypes ──

  getArchetypes(sessionId: string): Promise<ArchetypeListResponse> {
    return this.request<ArchetypeListResponse>(
      `/api/sessions/${sessionId}/archetypes`,
    );
  }

  // ── Events ──

  injectEvent(
    sessionId: string,
    body: InjectEventRequest,
  ): Promise<EventResponse> {
    return this.request<EventResponse>(
      `/api/sessions/${sessionId}/events`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  }

  // ── Posts ──

  getPosts(
    sessionId: string,
    offset = 0,
    limit = 20,
  ): Promise<PostListResponse> {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    return this.request<PostListResponse>(
      `/api/sessions/${sessionId}/posts?${params}`,
    );
  }

  // ── Zones (static, no session required) ──

  getZones(): Promise<GeoJSON.FeatureCollection> {
    return this.request<GeoJSON.FeatureCollection>("/api/zones");
  }
}

// ── WebSocket wrapper ────────────────────────────────────────────────────────

export type SocketState = "disconnected" | "connecting" | "connected";

export class SimulationSocket {
  private readonly wsUrl: string;
  private readonly sessionId: string;
  private readonly onMessage: (msg: WsIncoming) => void;
  private readonly onStateChange?: (state: SocketState) => void;

  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private state: SocketState = "disconnected";

  constructor(
    wsUrl: string,
    sessionId: string,
    onMessage: (msg: WsIncoming) => void,
    onStateChange?: (state: SocketState) => void,
  ) {
    // Strip trailing slash for consistent path concatenation
    this.wsUrl = wsUrl.replace(/\/$/, "");
    this.sessionId = sessionId;
    this.onMessage = onMessage;
    this.onStateChange = onStateChange;
  }

  connect(): void {
    // Avoid opening a second socket while one is already connecting or open
    if (
      this.ws !== null &&
      (this.ws.readyState === WebSocket.CONNECTING ||
        this.ws.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    this.setState("connecting");

    const socket = new WebSocket(
      `${this.wsUrl}/ws/${this.sessionId}`,
    );
    this.ws = socket;

    socket.onopen = () => {
      this.setState("connected");
      const subscribeMsg: WsOutgoing = { type: "subscribe" };
      socket.send(JSON.stringify(subscribeMsg));
    };

    socket.onmessage = (event: MessageEvent) => {
      let msg: WsIncoming;
      try {
        msg = JSON.parse(event.data as string) as WsIncoming;
      } catch {
        // Malformed frame — ignore
        return;
      }

      // Respond to server pings automatically
      if (msg.type === "ping") {
        const pong: WsOutgoing = { type: "pong" };
        socket.send(JSON.stringify(pong));
        // Also surface the ping to the caller so it can update last-seen time if needed
        this.onMessage(msg);
        return;
      }

      this.onMessage(msg);
    };

    socket.onerror = () => {
      // onerror is always followed by onclose — let onclose drive reconnect logic
    };

    socket.onclose = () => {
      this.setState("disconnected");
      this.ws = null;
      this.scheduleReconnect();
    };
  }

  disconnect(): void {
    this.clearReconnectTimer();

    if (this.ws !== null) {
      // Nullify onclose before closing so the close event does not trigger
      // an automatic reconnect after an intentional disconnect
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }

    this.setState("disconnected");
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 3000);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private setState(next: SocketState): void {
    if (this.state !== next) {
      this.state = next;
      this.onStateChange?.(next);
    }
  }
}
