import { useState, type FormEvent } from "react";
import { Confidence } from "../components/Confidence";
import { useLang, useT } from "../i18n";
import { copyText } from "../lib/clipboard";
import { analyseEnquiry, label, type EnquiryAnalysis, type Hub } from "../lib/models";
import { actOnEnquiry, addEnquiry, useStore, type Enquiry, type OperatorAction } from "../lib/store";

export function Inbox({ hub, onCreateBooking }: { hub: Hub; onCreateBooking: (e: Enquiry) => void }) {
  const t = useT();
  const lang = useLang();
  const { profile, enquiries } = useStore();
  const [text, setText] = useState("");
  const [contact, setContact] = useState("");
  const [current, setCurrent] = useState<Enquiry | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    const analysis = analyseEnquiry(hub, text.trim(), lang, profile); // ON DEVICE, no network
    const saved = addEnquiry(text.trim(), contact.trim(), analysis);
    setCurrent(saved);
    setText("");
    setContact("");
    setNotice(null);
  }

  async function act(enq: Enquiry, action: OperatorAction, sent: string | null) {
    if (sent) {
      const ok = await copyText(sent);
      setNotice(ok ? t("copied") : t("error"));
    }
    actOnEnquiry(enq.id, action, sent);
    setCurrent({ ...enq, status: "handled", operator_action: action, sent_text: sent });
  }

  return (
    <>
      <form className="card" onSubmit={onSubmit}>
        <h2>{t("inbox_title")}</h2>
        <p className="muted">{t("inbox_help")}</p>
        <label htmlFor="contact">{t("inbox_contact")}</label>
        <input id="contact" value={contact} onChange={(e) => setContact(e.target.value)} placeholder="+44 7700 900123 / Anna" />
        <label htmlFor="msg" style={{ marginTop: 12 }}>
          {t("inbox_text")}
        </label>
        <textarea id="msg" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("inbox_placeholder")} />
        <div className="row" style={{ marginTop: 12 }}>
          <button type="submit" disabled={!text.trim()}>
            {t("analyse")}
          </button>
        </div>
      </form>

      {notice && <div className="card notice">{notice}</div>}
      {current && <EnquiryCard hub={hub} enq={current} onAct={act} onCreateBooking={onCreateBooking} />}

      <section className="card">
        <h2>{t("recent_enquiries")}</h2>
        {enquiries.length === 0 && <p className="muted">{t("no_enquiries")}</p>}
        <ul className="list">
          {enquiries.slice(0, 20).map((e) => (
            <li key={e.id}>
              <button type="button" className="link" onClick={() => setCurrent(e)}>
                <span className={`chip ${e.status === "new" ? "chip-warn" : "chip-ok"}`}>{t(`status_${e.status}` as const)}</span>{" "}
                <span className="chip">{label(hub, "languages", e.analysis.language, lang)}</span>{" "}
                {e.analysis.intent ? <strong>{label(hub, "intents", e.analysis.intent, lang)}</strong> : <em>{t("unsure")}</em>}
                <div className="muted ellipsis">{e.text}</div>
              </button>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

function EnquiryCard({
  hub,
  enq,
  onAct,
  onCreateBooking,
}: {
  hub: Hub;
  enq: Enquiry;
  onAct: (e: Enquiry, a: OperatorAction, sent: string | null) => void;
  onCreateBooking: (e: Enquiry) => void;
}) {
  const t = useT();
  const lang = useLang();
  const a: EnquiryAnalysis = enq.analysis;
  const ask = a.decision === "ask_a_person";
  const [own, setOwn] = useState("");
  const [showOwn, setShowOwn] = useState(false);
  const [details, setDetails] = useState(false);
  const handled = enq.status === "handled";
  const bookingLike = a.intent === "booking" || a.intent === "availability";

  return (
    <div className={`card ${ask ? "result-ask" : "result-answer"}`} aria-live="polite">
      <blockquote className="quote">{enq.text}</blockquote>
      <div className="chips">
        <span className="chip">
          {t("detected_language")}: {label(hub, "languages", a.language, lang)} ({Math.round(a.language_confidence * 100)}%)
        </span>
        {enq.visitor_contact && <span className="chip">{enq.visitor_contact}</span>}
      </div>

      <h2 style={{ marginTop: 12 }}>{ask ? t("unsure_title") : t("visitor_wants")}</h2>
      {!ask && a.intent && <p className="big">{label(hub, "intents", a.intent, lang)}</p>}
      <p>{a.operator_summary}</p>
      <Confidence value={a.confidence} threshold={hub.threshold} />

      <button type="button" className="link small" onClick={() => setDetails(!details)}>
        {details ? t("hide_details") : t("show_details")}
      </button>
      {details && (
        <ul className="scores">
          {a.ranked.map((r) => (
            <li key={r.label}>
              <span>{label(hub, "intents", r.label, lang)}</span>
              <span className="muted">{Math.round(r.probability * 100)}%</span>
            </li>
          ))}
        </ul>
      )}

      {handled ? (
        <div className="sent">
          <span className="chip chip-ok">{t("status_handled")}</span>
          {enq.sent_text && <p className="reply">{enq.sent_text}</p>}
        </div>
      ) : (
        <>
          {a.reply_for_visitor && (
            <>
              <h3>{t("suggested_reply")}</h3>
              <p className="reply">{a.reply_for_visitor}</p>
              {a.reply_for_operator && a.reply_for_operator !== a.reply_for_visitor && (
                <>
                  <div className="muted">{t("reply_meaning")}</div>
                  <p className="reply reply-meaning">{a.reply_for_operator}</p>
                </>
              )}
            </>
          )}
          <h3>{t("holding_reply")}</h3>
          <p className="reply reply-meaning">{a.holding_reply}</p>

          <div className="row" style={{ marginTop: 12 }}>
            {a.reply_for_visitor && (
              <button type="button" onClick={() => onAct(enq, "send_standard", a.reply_for_visitor)}>
                {t("copy_send")}
              </button>
            )}
            <button type="button" className="secondary" onClick={() => onAct(enq, "send_holding", a.holding_reply)}>
              {t("send_holding")}
            </button>
            <button type="button" className="secondary" onClick={() => setShowOwn(!showOwn)}>
              {t("write_own")}
            </button>
            {bookingLike && (
              <button type="button" className="secondary" onClick={() => onCreateBooking(enq)}>
                {t("create_booking")}
              </button>
            )}
            <button type="button" className="ghost" onClick={() => onAct(enq, "dismiss", null)}>
              {t("dismiss")}
            </button>
          </div>
          {showOwn && (
            <div style={{ marginTop: 12 }}>
              <textarea value={own} onChange={(e) => setOwn(e.target.value)} placeholder={t("own_reply_placeholder")} />
              <button type="button" disabled={!own.trim()} onClick={() => onAct(enq, "send_custom", own.trim())} style={{ marginTop: 8 }}>
                {t("copy_send_own")}
              </button>
            </div>
          )}
        </>
      )}
      <p className="muted small" style={{ marginTop: 12 }}>
        {t("human_in_loop")} · {a.model_name}@{a.model_version}
      </p>
    </div>
  );
}
