import { useCallback, useEffect, useState } from "react";
import { api, type SmsMessage } from "../api/client";
import { useOnline } from "../hooks/useOnline";
import { useT } from "../i18n";

/** Simulates the basic-phone path against the backend: visitor SMS in, Kiswahili notification to Noor,
 *  Noor replies 1 / 2 / free text, visitor gets the fixed reply. Real gateways plug in behind the same endpoints. */
export function Sms() {
  const t = useT();
  const online = useOnline();
  const [log, setLog] = useState<SmsMessage[]>([]);
  const [meta, setMeta] = useState<{ provider: string; operator_number: string; service_number: string } | null>(null);
  const [visitorNumber, setVisitorNumber] = useState("+447700900123");
  const [visitorText, setVisitorText] = useState("Hi! How much is the coffee tour for 3 people on Saturday?");
  const [operatorText, setOperatorText] = useState("1");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await api.smsOutbox();
      setLog(r.messages);
      setMeta({ provider: r.provider, operator_number: r.operator_number, service_number: r.service_number });
      setErr(null);
    } catch {
      setErr(t("sms_offline"));
    }
  }, [t]);

  useEffect(() => {
    if (online) refresh();
  }, [online, refresh]);

  async function sendVisitor() {
    setBusy(true);
    try {
      await api.smsInbound(visitorNumber, visitorText);
      await refresh();
    } catch {
      setErr(t("error"));
    } finally {
      setBusy(false);
    }
  }

  async function sendOperator() {
    setBusy(true);
    try {
      await api.smsOperator(meta?.operator_number ?? "+000000000000", operatorText);
      await refresh();
    } catch {
      setErr(t("error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="card">
        <h2>{t("sms_title")}</h2>
        <p className="muted">{t("sms_help")}</p>
        {meta && <p className="muted small">{t("sms_provider", { provider: meta.provider })} · {meta.service_number} → {meta.operator_number}</p>}
        {err && <p className="notice-inline">{err}</p>}
        <div className="grid2">
          <div>
            <label>{t("sms_visitor_number")}</label>
            <input value={visitorNumber} onChange={(e) => setVisitorNumber(e.target.value)} />
          </div>
          <div className="span2">
            <label>{t("sms_visitor_text")}</label>
            <textarea value={visitorText} onChange={(e) => setVisitorText(e.target.value)} style={{ minHeight: 64 }} />
          </div>
          <div className="span2">
            <button type="button" onClick={sendVisitor} disabled={busy || !online}>
              {t("sms_send_visitor")}
            </button>
          </div>
          <div className="span2">
            <label>{t("sms_operator_text")}</label>
            <input value={operatorText} onChange={(e) => setOperatorText(e.target.value)} />
          </div>
          <div className="span2 row">
            <button type="button" className="secondary" onClick={sendOperator} disabled={busy || !online}>
              {t("sms_send_operator")}
            </button>
            <button type="button" className="ghost" onClick={refresh} disabled={!online}>
              {t("refresh")}
            </button>
          </div>
        </div>
      </section>

      <section className="card">
        <h3>{t("sms_log")}</h3>
        <div className="smslog">
          {log.map((m) => (
            <div key={m.id} className={`sms ${m.direction}`}>
              <div className="muted small">
                {m.created_at.slice(11, 19)} · {m.direction === "out" ? t("sms_to") : t("sms_from")} {m.counterpart} · {m.purpose}
              </div>
              <div>{m.text}</div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
