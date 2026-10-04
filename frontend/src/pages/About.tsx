import { useEffect, useState } from "react";
import { api, type Dataset } from "../api/client";
import { useOnline } from "../hooks/useOnline";
import { useT } from "../i18n";
import type { Hub } from "../lib/models";

export function About({ hub }: { hub: Hub }) {
  const t = useT();
  const online = useOnline();
  const [datasets, setDatasets] = useState<Dataset[] | null>(null);
  const kb = Math.round(hub.totalBytes / 1024);
  const pct = Math.round(hub.threshold * 100);

  useEffect(() => {
    if (!online) return;
    api.datasets().then(setDatasets).catch(() => setDatasets(null));
  }, [online]);

  const models = [hub.intent, hub.langid, hub.aspect, hub.sentiment];
  const m = (x: Record<string, unknown>, k: string) => (typeof x[k] === "number" ? `${Math.round((x[k] as number) * 100)}%` : "—");

  return (
    <>
      <section className="card">
        <h2>{t("about_title")}</h2>
        <p>{t("about_what")}</p>
        <h3>{t("about_rules")}</h3>
        <ul className="ticks">
          <li>{t("rule_device")}</li>
          <li>{t("rule_offline")}</li>
          <li>{t("rule_small", { kb })}</li>
          <li>{t("rule_language")}</li>
        </ul>
        <h3>{t("about_guardrails")}</h3>
        <ul className="ticks">
          <li>{t("guard_1")}</li>
          <li>{t("guard_2", { pct })}</li>
          <li>{t("guard_3")}</li>
          <li>{t("guard_4")}</li>
        </ul>
      </section>

      <section className="card">
        <h3>{t("about_models")}</h3>
        <table className="clauses">
          <thead>
            <tr>
              <th>{t("model")}</th>
              <th>{t("size")}</th>
              <th>{t("holdout_acc")}</th>
              <th>{t("coverage_short")}</th>
              <th>{t("acc_when_answering")}</th>
            </tr>
          </thead>
          <tbody>
            {models.map((x) => (
              <tr key={x.name}>
                <td>
                  <strong>{x.name}</strong>
                  <div className="muted small">{x.task}</div>
                </td>
                <td>{Math.round(x.sizeBytes / 1024)} KB</td>
                <td>{m(x.metrics, "accuracy")}</td>
                <td>{m(x.metrics, "coverage_at_threshold")}</td>
                <td>{m(x.metrics, "accuracy_when_answering")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">{t("about_models_note")}</p>
      </section>

      <section className="card">
        <h3>{t("about_data")}</h3>
        {!datasets && <p className="muted">{t("about_data_offline")}</p>}
        {datasets?.map((d) => (
          <div key={d.name} className="dataset">
            <strong>{d.name}</strong> <span className="chip">{d.kind.replace("_", " ")}</span>
            <div className="small">{d.how_we_use_it}</div>
            <div className="muted small">
              <em>Gaps:</em> {d.coverage_gaps}
            </div>
            <div className="muted small">
              {d.license}
              {d.size ? ` · ${d.size}` : ""}
            </div>
          </div>
        ))}
      </section>

      <section className="card">
        <h3>{t("about_data_handling")}</h3>
        <ul className="ticks">
          <li>{t("data_1")}</li>
          <li>{t("data_2")}</li>
          <li>{t("data_3")}</li>
        </ul>
        <h3>{t("about_localising")}</h3>
        <p>{t("localising_text")}</p>
      </section>
    </>
  );
}
