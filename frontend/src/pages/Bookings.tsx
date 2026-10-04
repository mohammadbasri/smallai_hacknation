import { useEffect, useState, type FormEvent } from "react";
import { useT } from "../i18n";
import { copyText } from "../lib/clipboard";
import { special, type Hub } from "../lib/models";
import { addBooking, updateBooking, useStore, type Booking, type BookingStatus, type Enquiry } from "../lib/store";

type MsgKind = "booking_confirmed" | "booking_reminder" | "booking_cancelled" | "followup";

const today = () => new Date().toISOString().slice(0, 10);

export function Bookings({ hub, prefill, onPrefillUsed }: { hub: Hub; prefill: Enquiry | null; onPrefillUsed: () => void }) {
  const t = useT();
  const { bookings, profile } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ visitor_name: "", visitor_contact: "", language: "en", date: today(), time: "09:00", party_size: 2, notes: "", enquiry_id: null as string | null });
  const [notice, setNotice] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ id: string; kind: MsgKind; text: string } | null>(null);

  useEffect(() => {
    if (prefill) {
      setForm((f) => ({
        ...f,
        visitor_contact: prefill.visitor_contact,
        language: prefill.analysis.language_supported ? prefill.analysis.language : "en",
        notes: prefill.text,
        enquiry_id: prefill.id,
      }));
      setShowForm(true);
      onPrefillUsed();
    }
  }, [prefill, onPrefillUsed]);

  function submit(e: FormEvent) {
    e.preventDefault();
    addBooking({ ...form, status: "pending", source: form.enquiry_id ? "enquiry" : "app" });
    setShowForm(false);
    setForm({ visitor_name: "", visitor_contact: "", language: "en", date: today(), time: "09:00", party_size: 2, notes: "", enquiry_id: null });
  }

  function setStatus(b: Booking, status: BookingStatus) {
    updateBooking(b.id, { status });
  }

  async function showMessage(b: Booking, kind: MsgKind) {
    const text = special(hub, kind, b.language, profile, { date: b.date, time: b.time, party_size: b.party_size });
    setMsg({ id: b.id, kind, text });
    const ok = await copyText(text);
    setNotice(ok ? t("copied") : null);
  }

  const upcoming = bookings.filter((b) => (b.status === "pending" || b.status === "confirmed") && b.date >= today());
  const past = bookings.filter((b) => !upcoming.includes(b));

  return (
    <>
      <section className="card">
        <h2>{t("bookings_title")}</h2>
        <p className="muted">{t("bookings_help")}</p>
        {!showForm && (
          <button type="button" onClick={() => setShowForm(true)}>
            {t("add_booking")}
          </button>
        )}
        {showForm && (
          <form onSubmit={submit} className="grid2">
            <div>
              <label>{t("visitor_name")}</label>
              <input value={form.visitor_name} onChange={(e) => setForm({ ...form, visitor_name: e.target.value })} />
            </div>
            <div>
              <label>{t("visitor_contact")}</label>
              <input value={form.visitor_contact} onChange={(e) => setForm({ ...form, visitor_contact: e.target.value })} />
            </div>
            <div>
              <label>{t("visitor_language")}</label>
              <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
                <option value="en">English</option>
                <option value="fr">Français</option>
                <option value="sw">Kiswahili</option>
              </select>
            </div>
            <div>
              <label>{t("party_size")}</label>
              <input type="number" min={1} max={50} value={form.party_size} onChange={(e) => setForm({ ...form, party_size: Number(e.target.value) })} />
            </div>
            <div>
              <label>{t("date")}</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
            </div>
            <div>
              <label>{t("time")}</label>
              <input type="time" value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} />
            </div>
            <div className="span2">
              <label>{t("notes")}</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} style={{ minHeight: 64 }} />
            </div>
            <div className="row span2">
              <button type="submit">{t("save")}</button>
              <button type="button" className="secondary" onClick={() => setShowForm(false)}>
                {t("cancel")}
              </button>
            </div>
          </form>
        )}
      </section>

      {notice && <div className="card notice">{notice}</div>}
      {msg && (
        <div className="card result-answer">
          <h3>{t(`message_${msg.kind.replace("booking_", "")}` as "message_confirmed")}</h3>
          <p className="reply">{msg.text}</p>
          <button type="button" className="secondary" onClick={() => copyText(msg.text).then((ok) => setNotice(ok ? t("copied") : null))}>
            {t("copy")}
          </button>
        </div>
      )}

      <section className="card">
        <h3>{t("upcoming")}</h3>
        {upcoming.length === 0 && <p className="muted">{t("no_bookings")}</p>}
        {upcoming.map((b) => (
          <BookingRow key={b.id} b={b} onStatus={setStatus} onMessage={showMessage} />
        ))}
      </section>
      {past.length > 0 && (
        <section className="card">
          <h3>{t("past")}</h3>
          {past.map((b) => (
            <BookingRow key={b.id} b={b} onStatus={setStatus} onMessage={showMessage} />
          ))}
        </section>
      )}
    </>
  );
}

function BookingRow({ b, onStatus, onMessage }: { b: Booking; onStatus: (b: Booking, s: BookingStatus) => void; onMessage: (b: Booking, k: MsgKind) => void }) {
  const t = useT();
  return (
    <div className="booking">
      <div className="booking-head">
        <strong>
          {b.date} · {b.time}
        </strong>
        <span className={`chip ${b.status === "confirmed" ? "chip-ok" : b.status === "cancelled" ? "chip-bad" : "chip-warn"}`}>
          {t(`status_${b.status}` as const)}
        </span>
      </div>
      <div>
        {b.visitor_name || "—"} · {b.party_size} {t("party_size").toLowerCase()} · {b.language.toUpperCase()}
        {b.visitor_contact && <span className="muted"> · {b.visitor_contact}</span>}
      </div>
      {b.notes && <div className="muted small ellipsis">{b.notes}</div>}
      <div className="row small-actions">
        {b.status === "pending" && (
          <button type="button" onClick={() => onStatus(b, "confirmed")}>
            {t("mark_confirmed")}
          </button>
        )}
        {(b.status === "pending" || b.status === "confirmed") && (
          <>
            <button type="button" className="secondary" onClick={() => onMessage(b, "booking_confirmed")}>
              {t("message_confirmed")}
            </button>
            <button type="button" className="secondary" onClick={() => onMessage(b, "booking_reminder")}>
              {t("message_reminder")}
            </button>
            <button type="button" className="secondary" onClick={() => onStatus(b, "completed")}>
              {t("mark_completed")}
            </button>
            <button type="button" className="ghost" onClick={() => onStatus(b, "cancelled")}>
              {t("mark_cancelled")}
            </button>
          </>
        )}
        {b.status === "cancelled" && (
          <button type="button" className="secondary" onClick={() => onMessage(b, "booking_cancelled")}>
            {t("message_cancelled")}
          </button>
        )}
        {b.status === "completed" && (
          <button type="button" className="secondary" onClick={() => onMessage(b, "followup")}>
            {t("message_followup")}
          </button>
        )}
      </div>
    </div>
  );
}
