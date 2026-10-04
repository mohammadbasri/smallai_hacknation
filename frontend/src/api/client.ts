/** Thin typed client for the FastAPI backend. Mirrors backend/app/schemas.py.
 *  The app works without it (models run on device); the API is for sync, the SMS channel and parity checks. */

export type RecordKind = "enquiry" | "booking" | "feedback" | "profile";

export interface QueuedRecord {
  id: string;
  kind: RecordKind;
  payload: Record<string, unknown>;
  captured_at: string;
  language: string;
}

export interface SyncResponse {
  accepted: string[];
  rejected: Record<string, string>;
}

export interface SmsMessage {
  id: number;
  created_at: string;
  direction: "in" | "out";
  counterpart: string;
  text: string;
  language: string;
  purpose: string;
}

export interface Dataset {
  name: string;
  kind: "problem_evidence" | "build_data" | "benchmark";
  what_it_is: string;
  why_it_matters: string;
  how_we_use_it: string;
  license: string;
  size: string;
  url: string;
  coverage_gaps: string;
}

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; models: string[]; sms_provider: string }>("/health"),
  sync: (client_id: string, records: QueuedRecord[]) =>
    request<SyncResponse>("/sync", { method: "POST", body: JSON.stringify({ client_id, records }) }),
  datasets: () => request<Dataset[]>("/datasets"),
  smsOutbox: () =>
    request<{ provider: string; operator_number: string; service_number: string; messages: SmsMessage[] }>("/sms/outbox"),
  smsInbound: (from: string, text: string) =>
    request<{ ok: boolean; enquiry_id?: string; operator_sms?: SmsMessage }>("/sms/inbound", {
      method: "POST",
      body: JSON.stringify({ from, text }),
    }),
  smsOperator: (from: string, text: string) =>
    request<{ ok: boolean; operator_action?: string; sent_text?: string }>("/sms/operator", {
      method: "POST",
      body: JSON.stringify({ from, text }),
    }),
};
