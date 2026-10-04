import { useT } from "../i18n";

/** Never hide the confidence: a confident wrong answer is the failure mode the brief warns about. */
export function Confidence({ value, threshold }: { value: number; threshold: number }) {
  const t = useT();
  const pct = Math.round(value * 100);
  const ok = value >= threshold;
  return (
    <div className="confidence">
      <div className="muted">{t("confidence", { pct })}</div>
      <div className="meter" aria-hidden="true">
        <div className={ok ? "ok" : "warn"} style={{ width: `${pct}%` }} />
        <span className="meter-threshold" style={{ left: `${Math.round(threshold * 100)}%` }} />
      </div>
    </div>
  );
}
