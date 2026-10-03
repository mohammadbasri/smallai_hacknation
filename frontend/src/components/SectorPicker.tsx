import type { Sector } from "../api/client";
import { useT } from "../i18n";

const SECTORS: Sector[] = ["health", "agriculture", "tourism"];

export function SectorPicker({ value, onChange }: { value: Sector; onChange: (s: Sector) => void }) {
  const t = useT();
  return (
    <div>
      <label>{t("choose_sector")}</label>
      <div className="sectors" role="radiogroup">
        {SECTORS.map((s) => (
          <button
            key={s}
            type="button"
            role="radio"
            aria-checked={value === s}
            className={value === s ? "active" : ""}
            onClick={() => onChange(s)}
          >
            {t(`sector_${s}` as const)}
          </button>
        ))}
      </div>
    </div>
  );
}
