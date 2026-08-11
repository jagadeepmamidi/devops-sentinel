import type { HealthCheck, Incident, ListResponse, SentinelClientOptions } from "./types.js";

export class SentinelError extends Error {
  constructor(public readonly status: number, message: string, public readonly details?: unknown) {
    super(message);
    this.name = "SentinelError";
  }
}

export class SentinelClient {
  private readonly baseUrl: string;
  private readonly token?: string;
  private readonly request: typeof globalThis.fetch;

  constructor(options: SentinelClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\\/$/, "");
    this.token = options.token;
    this.request = options.fetch ?? globalThis.fetch;
    if (!this.request) throw new Error("Global fetch is unavailable; provide options.fetch.");
  }

  async healthCheck(url: string, timeout = 10): Promise<HealthCheck> {
    return this.call<HealthCheck>(`/api/quick-check?url=${encodeURIComponent(url)}&timeout=${timeout}`);
  }

  async listIncidents(params: { limit?: number; severity?: string; status?: string } = {}): Promise<ListResponse<Incident>> {
    const query = new URLSearchParams();
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.severity) query.set("severity", params.severity);
    if (params.status) query.set("status", params.status);
    return this.call<ListResponse<Incident>>(`/api/incidents?${query}`);
  }

  async getIncident(id: string): Promise<Incident> {
    return this.call<Incident>(`/api/incidents/${encodeURIComponent(id)}`);
  }

  async getIncidentEvents(id: string): Promise<ListResponse<unknown>> {
    return this.call<ListResponse<unknown>>(`/api/incidents/${encodeURIComponent(id)}/events`);
  }

  async generatePostmortem(incidentId: string, resolutionNotes?: string): Promise<Record<string, unknown>> {
    return this.call<Record<string, unknown>>("/api/postmortems/generate", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, resolution_notes: resolutionNotes }),
    });
  }

  private async call<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await this.request(`${this.baseUrl}${path}`, {
      ...init,
      headers: { Accept: "application/json", "Content-Type": "application/json", ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}), ...init.headers },
    });
    const body: unknown = await response.json().catch(() => undefined);
    if (!response.ok) {
      const message = typeof body === "object" && body !== null && "detail" in body ? String(body.detail) : response.statusText;
      throw new SentinelError(response.status, message, body);
    }
    return body as T;
  }
}
