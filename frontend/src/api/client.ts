/** Thin typed client for the FastAPI backend. Mirrors backend/app/schemas.py. */

export type Sector = "tourism";
export type Decision = "answer" | "ask_a_person";

export interface InferenceRequest {
  sector: Sector;
  text: string;
  language: string;
  client_id?: string;
}

export interface InferenceResponse {
  decision: Decision;
  label: string | null;
  confidence: number;
  explanation: string;
  language: string;
  model_name: string;
  model_version: string;
  sources: string[];
}

export interface QueuedRecord {
  id: string;
  sector: Sector;
  payload: Record<string, unknown>;
  captured_at: string;
  language: string;
}

export interface SyncResponse {
  accepted: string[];
  rejected: Record<string, string>;
}

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  infer: (body: InferenceRequest) => request<InferenceResponse>("/inference", { method: "POST", body: JSON.stringify(body) }),
  labels: (sector: Sector) => request<{ sector: Sector; labels: string[] }>(`/inference/labels/${sector}`),
  sync: (client_id: string, records: QueuedRecord[]) =>
    request<SyncResponse>("/sync", { method: "POST", body: JSON.stringify({ client_id, records }) }),
};
