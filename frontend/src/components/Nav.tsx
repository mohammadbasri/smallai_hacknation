import { useT } from "../i18n";

export type Page = "inbox" | "bookings" | "feedback" | "listing" | "sms" | "about";

const PAGES: { id: Page; icon: string }[] = [
  { id: "inbox", icon: "✉" },
  { id: "bookings", icon: "📅" },
  { id: "feedback", icon: "★" },
  { id: "listing", icon: "☕" },
  { id: "sms", icon: "📟" },
  { id: "about", icon: "ⓘ" },
];

export function Nav({ page, onChange, badge }: { page: Page; onChange: (p: Page) => void; badge?: Partial<Record<Page, number>> }) {
  const t = useT();
  return (
    <nav className="nav" aria-label="Main">
      {PAGES.map((p) => (
        <button key={p.id} type="button" className={page === p.id ? "active" : ""} onClick={() => onChange(p.id)} aria-current={page === p.id}>
          <span className="nav-icon" aria-hidden="true">
            {p.icon}
          </span>
          <span>{t(`nav_${p.id}` as const)}</span>
          {badge?.[p.id] ? <span className="nav-badge">{badge[p.id]}</span> : null}
        </button>
      ))}
    </nav>
  );
}
