import { useMemo, useState, type FormEvent } from "react";
import { useLang, useT } from "../i18n";
import { analyseFeedback, label, summarise, type ClauseAnalysis, type Hub } from "../lib/models";
import { addReview, loadSampleReviews, removeReview, useStore } from "../lib/store";

export function Feedback({ hub }: { hub: Hub }) {
  const t = useT();
  const lang = useLang();
  const { reviews } = useStore();
  const [text, setText] = useState("");
  const [preview, setPreview] = useState<{ language: string; clauses: ClauseAnalysis[] } | null>(null);

  const summary = useMemo(() => summarise(hub, reviews), [hub, reviews]);

  function analyse(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setPreview(analyseFeedback(hub, text.trim())); // ON DEVICE
  }

  function save() {
    if (!preview) return;
    addReview(text.trim(), preview.language, preview.clauses);
    setText("");
    setPreview(null);
  }

  return (
    <>
      <form className="card" onSubmit={analyse}>
        <h2>{t("feedback_title")}</h2>
        <p className="muted">{t("feedback_help")}</p>
        <label htmlFor="review">{t("feedback_text")}</label>
        <textarea id="review" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("feedback_placeholder")} />
        <div className="row" style={{ marginTop: 12 }}>
          <button type="submit" disabled={!text.trim()}>
            {t("analyse_feedback")}
          </button>
          {preview && (
            <button type="button" className="secondary" onClick={save}>
              {t("save_feedback")}
            </button>
          )}
        </div>
      </form>

      {preview && <ClauseTable hub={hub} clauses={preview.clauses} language={preview.language} />}

      <section className="card">
        <h2>{t("summary_title")}</h2>
        {reviews.length === 0 ? (
          <>
            <p className="muted">{t("no_reviews")}</p>
            <button type="button" className="secondary" onClick={() => loadSampleReviews((s) => analyseFeedback(hub, s))}>
              {t("load_samples")}
            </button>
          </>
        ) : (
          <>
            <p className="muted">{t("coverage", { confident: summary.n_confident, total: summary.n_clauses, unsure: summary.n_unsure })}</p>
            <div className="grid2">
              <div>
                <h3 className="ok-text">{t("keep_doing")}</h3>
                {summary.keep_doing.map((a) => (
                  <div key={a.aspect} className="insight">
                    <strong>{label(hub, "aspects", a.aspect, lang)}</strong>
                    <div className="muted small">{t("mentions", { pos: a.positive, neg: a.negative })}</div>
                    {a.examples_positive.slice(0, 2).map((x, i) => (
                      <div key={i} className="quote small">
                        “{x}”
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <div>
                <h3 className="warn-text">{t("fix_next")}</h3>
                {summary.fix_next.map((a) => (
                  <div key={a.aspect} className="insight">
                    <strong>{label(hub, "aspects", a.aspect, lang)}</strong>
                    <div className="muted small">{t("mentions", { pos: a.positive, neg: a.negative })}</div>
                    {a.examples_negative.slice(0, 2).map((x, i) => (
                      <div key={i} className="quote small">
                        “{x}”
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
            <div className="bars">
              {summary.aspects.map((a) => {
                const total = Math.max(1, a.positive + a.negative);
                return (
                  <div key={a.aspect} className="bar-row">
                    <span className="bar-label">{label(hub, "aspects", a.aspect, lang)}</span>
                    <span className="bar">
                      <span className="bar-pos" style={{ width: `${(a.positive / total) * 100}%` }} />
                      <span className="bar-neg" style={{ width: `${(a.negative / total) * 100}%` }} />
                    </span>
                    <span className="muted small">
                      {a.positive}/{a.negative}
                    </span>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </section>

      {reviews.length > 0 && (
        <section className="card">
          <h3>{t("saved_reviews")}</h3>
          {reviews.map((r) => (
            <div key={r.id} className="review">
              <div className="muted small">
                {r.created_at.slice(0, 10)} · {label(hub, "languages", r.language, lang)} · {r.source}
              </div>
              <div className="ellipsis">{r.text}</div>
              <button type="button" className="ghost small" onClick={() => removeReview(r.id)}>
                {t("delete")}
              </button>
            </div>
          ))}
        </section>
      )}
    </>
  );
}

function ClauseTable({ hub, clauses, language }: { hub: Hub; clauses: ClauseAnalysis[]; language: string }) {
  const t = useT();
  const lang = useLang();
  return (
    <section className="card">
      <div className="chips">
        <span className="chip">
          {t("detected_language")}: {label(hub, "languages", language, lang)}
        </span>
      </div>
      <table className="clauses">
        <thead>
          <tr>
            <th>{t("clause")}</th>
            <th>{t("aspect")}</th>
            <th>{t("sentiment")}</th>
          </tr>
        </thead>
        <tbody>
          {clauses.map((c, i) => (
            <tr key={i}>
              <td>{c.text}</td>
              <td>
                {c.aspect ? (
                  <span className="chip">{label(hub, "aspects", c.aspect, lang)}</span>
                ) : (
                  <span className="chip chip-warn">{t("unsure")}</span>
                )}
                <div className="muted small">{Math.round(c.aspect_confidence * 100)}%</div>
              </td>
              <td>
                {c.sentiment ? (
                  <span className={`chip ${c.sentiment === "positive" ? "chip-ok" : "chip-bad"}`}>
                    {c.sentiment === "positive" ? t("liked") : t("disliked")}
                  </span>
                ) : (
                  <span className="chip chip-warn">{t("unsure")}</span>
                )}
                <div className="muted small">{Math.round(c.sentiment_confidence * 100)}%</div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
