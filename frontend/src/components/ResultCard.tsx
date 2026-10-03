import type { InferenceResponse } from "../api/client";
import { useT } from "../i18n";

/** Shows the model's suggestion OR the human-in-the-loop fallback.
 *  Never hides the confidence: a confident wrong answer is the failure mode the brief warns about. */
export function ResultCard({ result }: { result: InferenceResponse }) {
  const t = useT();
  const ask = result.decision === "ask_a_person";
  const pct = Math.round(result.confidence * 100);

  return (
    <div className={`card ${ask ? "result-ask" : "result-answer"}`} aria-live="polite">
      <h2 style={{ marginTop: 0 }}>{ask ? t("ask_person_title") : t("result_title")}</h2>
      {!ask && result.label && <p style={{ fontSize: "1.1rem", fontWeight: 600 }}>{result.label.replace(/_/g, " ")}</p>}
      <p>{result.explanation}</p>

      <div className="muted">{t("confidence", { pct })}</div>
      <div className="meter" aria-hidden="true">
        <div style={{ width: `${pct}%` }} />
      </div>

      {result.sources.length > 0 && (
        <p className="muted">
          {t("sources")}: {result.sources.join("; ")}
        </p>
      )}
      <p className="muted">
        {t("human_in_loop")} · {result.model_name}@{result.model_version}
      </p>
    </div>
  );
}
