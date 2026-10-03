import { useOnline } from "../hooks/useOnline";
import { useT } from "../i18n";

export function OnlineBadge() {
  const online = useOnline();
  const t = useT();
  return <span className={`badge ${online ? "online" : "offline"}`}>{online ? t("online") : t("offline")}</span>;
}
