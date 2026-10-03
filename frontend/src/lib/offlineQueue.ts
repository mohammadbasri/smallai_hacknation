/** Store-and-forward queue: save now, send later (see brief glossary).
 *  Records live in localStorage until the backend acknowledges them.
 *  Swap for IndexedDB if you need to queue images or audio. */
import { api, type QueuedRecord, type Sector } from "../api/client";

const KEY = "smallai.queue";
const CLIENT_KEY = "smallai.client_id";

function read(): QueuedRecord[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]") as QueuedRecord[];
  } catch {
    return [];
  }
}

function write(records: QueuedRecord[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(records));
  } catch {
    /* storage full or unavailable: keep in memory only */
  }
}

export function getClientId(): string {
  try {
    let id = localStorage.getItem(CLIENT_KEY);
    if (!id) {
      id = crypto.randomUUID ? crypto.randomUUID() : `dev-${Date.now()}`;
      localStorage.setItem(CLIENT_KEY, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

export function enqueue(sector: Sector, payload: Record<string, unknown>, language: string): QueuedRecord {
  const rec: QueuedRecord = {
    id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
    sector,
    payload,
    captured_at: new Date().toISOString(),
    language,
  };
  write([...read(), rec]);
  return rec;
}

export function pending(): QueuedRecord[] {
  return read();
}

/** Push everything queued; keep whatever the server did not accept. Returns number accepted. */
export async function flush(): Promise<number> {
  const records = read();
  if (records.length === 0) return 0;
  const res = await api.sync(getClientId(), records);
  const accepted = new Set(res.accepted);
  write(records.filter((r) => !accepted.has(r.id)));
  return accepted.size;
}
