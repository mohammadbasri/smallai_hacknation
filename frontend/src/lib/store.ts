/** Offline-first local state (localStorage) with a tiny subscription hook.
 *  Every mutation also queues a sync record so the backend mirrors the phone when a signal appears. */
import { useSyncExternalStore } from "react";
import type { ClauseAnalysis, EnquiryAnalysis } from "./models";
import { enqueue, newId } from "./offlineQueue";

export interface Profile {
  farm_name: string;
  operator_name: string;
  village: string;
  phone: string;
  languages: string;
  price_adult: string;
  price_child: string;
  currency: string;
  duration: string;
  includes: string;
  open_days: string;
  start_times: string;
  location_hint: string;
  directions_hint: string;
  dietary_note: string;
  max_party: number;
}

export const DEFAULT_PROFILE: Profile = {
  farm_name: "Noor's Coffee Farm",
  operator_name: "Noor",
  village: "Ondera highlands",
  phone: "+000 000 000",
  languages: "Kiswahili, English (via guide), French (via guide)",
  price_adult: "15",
  price_child: "5",
  currency: "USD",
  duration: "2.5 hours",
  includes: "farm walk, coffee picking (in season), roasting demonstration, tasting, tea on arrival",
  open_days: "Tuesday to Sunday",
  start_times: "9:00 and 14:00",
  location_hint: "Ondera Coffee Cooperative road, 20 minutes from the district town",
  directions_hint: "Turn left at the cooperative sign and follow the murram road uphill for 3 km",
  dietary_note: "Vegetarian lunch is available on request. The walk is on uneven paths with some steep sections.",
  max_party: 12,
};

export type EnquiryStatus = "new" | "handled";
export type OperatorAction = "send_standard" | "send_holding" | "send_custom" | "dismiss";

export interface Enquiry {
  id: string;
  created_at: string;
  source: string;
  visitor_contact: string;
  text: string;
  analysis: EnquiryAnalysis;
  status: EnquiryStatus;
  operator_action: OperatorAction | null;
  sent_text: string | null;
}

export type BookingStatus = "pending" | "confirmed" | "cancelled" | "completed";

export interface Booking {
  id: string;
  created_at: string;
  updated_at: string;
  visitor_name: string;
  visitor_contact: string;
  language: string;
  date: string;
  time: string;
  party_size: number;
  status: BookingStatus;
  notes: string;
  source: string;
  enquiry_id: string | null;
}

export interface Review {
  id: string;
  created_at: string;
  source: string;
  visitor_contact: string;
  text: string;
  language: string;
  clauses: ClauseAnalysis[];
}

interface State {
  profile: Profile;
  enquiries: Enquiry[];
  bookings: Booking[];
  reviews: Review[];
}

const KEY = "karibu.state";
let state: State = load();
const listeners = new Set<() => void>();

function load(): State {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<State>;
      return {
        profile: { ...DEFAULT_PROFILE, ...(parsed.profile ?? {}) },
        enquiries: parsed.enquiries ?? [],
        bookings: parsed.bookings ?? [],
        reviews: parsed.reviews ?? [],
      };
    }
  } catch {
    /* fall through */
  }
  return { profile: DEFAULT_PROFILE, enquiries: [], bookings: [], reviews: [] };
}

function commit(next: State) {
  state = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* storage unavailable: keep in memory */
  }
  listeners.forEach((l) => l());
}

export function useStore(): State {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
    () => state
  );
}

const now = () => new Date().toISOString();

// ----------------------------------------------------------------------------- profile
export function saveProfile(p: Profile) {
  commit({ ...state, profile: p });
  enqueue("profile", "profile", p as unknown as Record<string, unknown>, "sw");
}

// ----------------------------------------------------------------------------- enquiries
function enquiryPayload(e: Enquiry): Record<string, unknown> {
  return {
    created_at: e.created_at,
    source: e.source,
    visitor_contact: e.visitor_contact,
    text: e.text,
    language: e.analysis.language,
    intent: e.analysis.intent,
    confidence: e.analysis.confidence,
    decision: e.analysis.decision,
    reply_for_visitor: e.analysis.reply_for_visitor,
    status: e.status,
    operator_action: e.operator_action,
    sent_text: e.sent_text,
  };
}

export function addEnquiry(text: string, visitor_contact: string, analysis: EnquiryAnalysis, source = "app"): Enquiry {
  const e: Enquiry = {
    id: newId(),
    created_at: now(),
    source,
    visitor_contact,
    text,
    analysis,
    status: "new",
    operator_action: null,
    sent_text: null,
  };
  commit({ ...state, enquiries: [e, ...state.enquiries] });
  enqueue("enquiry", e.id, enquiryPayload(e), analysis.language);
  return e;
}

export function actOnEnquiry(id: string, action: OperatorAction, sentText: string | null) {
  const enquiries = state.enquiries.map((e) =>
    e.id === id ? { ...e, status: "handled" as const, operator_action: action, sent_text: sentText } : e
  );
  commit({ ...state, enquiries });
  const e = enquiries.find((x) => x.id === id);
  if (e) enqueue("enquiry", e.id, enquiryPayload(e), e.analysis.language);
}

// ----------------------------------------------------------------------------- bookings
function bookingPayload(b: Booking): Record<string, unknown> {
  const { id: _id, ...rest } = b;
  return rest;
}

export function addBooking(input: Omit<Booking, "id" | "created_at" | "updated_at">): Booking {
  const b: Booking = { ...input, id: newId(), created_at: now(), updated_at: now() };
  commit({ ...state, bookings: [...state.bookings, b].sort((x, y) => (x.date + x.time).localeCompare(y.date + y.time)) });
  enqueue("booking", b.id, bookingPayload(b), b.language);
  return b;
}

export function updateBooking(id: string, patch: Partial<Booking>) {
  const bookings = state.bookings.map((b) => (b.id === id ? { ...b, ...patch, updated_at: now() } : b));
  commit({ ...state, bookings });
  const b = bookings.find((x) => x.id === id);
  if (b) enqueue("booking", b.id, bookingPayload(b), b.language);
}

// ----------------------------------------------------------------------------- reviews
export function addReview(text: string, language: string, clauses: ClauseAnalysis[], source = "paste", visitor_contact = ""): Review {
  const r: Review = { id: newId(), created_at: now(), source, visitor_contact, text, language, clauses };
  commit({ ...state, reviews: [r, ...state.reviews] });
  enqueue("feedback", r.id, { created_at: r.created_at, source, visitor_contact, text, language, clauses }, language);
  return r;
}

export function removeReview(id: string) {
  commit({ ...state, reviews: state.reviews.filter((r) => r.id !== id) });
}

/** Demo helper: load a handful of realistic reviews so the summary has something to show. */
export function loadSampleReviews(analyse: (text: string) => { language: string; clauses: ClauseAnalysis[] }) {
  const samples = [
    "The coffee tasting was the highlight of our trip. Noor and her family were incredibly welcoming. The road was terrible though, you need a 4x4.",
    "Lovely walk through the coffee trees and the kids loved picking cherries. Lunch was cold and very basic. Great value for money.",
    "La dégustation de café était le point fort. Le guide parlait très bien français. La marche était beaucoup trop longue pour notre groupe.",
    "Tulifurahia sana ziara. Kahawa bora kabisa niliyowahi kunywa. Hakuna alama zozote barabarani, tulipita mara mbili.",
    "Booking by WhatsApp was quick and easy and they confirmed within an hour. The guide's English was hard to follow. Best cup of coffee I have ever had.",
    "We felt like guests, not customers. The map pin was in the wrong place. The roasting demo over the fire was magical.",
  ];
  for (const s of samples) {
    const a = analyse(s);
    addReview(s, a.language, a.clauses, "sample");
  }
}
