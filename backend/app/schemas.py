"""Pydantic models shared by the API routers. Mirrored in frontend/src/api/client.ts."""
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Decision(str, Enum):
    """Human-in-the-loop outcome. The tool informs; a person decides."""

    answer = "answer"  # confident enough to show a suggestion
    ask_a_person = "ask_a_person"  # "not sure, ask a person"


Lang = Literal["en", "fr", "sw", "other"]


# --------------------------------------------------------------------------- enquiries
class EnquiryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Visitor message (SMS, WhatsApp, email...)")
    operator_language: str = Field("sw", min_length=2, max_length=8, description="Language Noor reads")
    client_id: str | None = None


class Ranked(BaseModel):
    label: str
    probability: float


class EnquiryAnalysis(BaseModel):
    decision: Decision
    language: str = Field(..., description="Detected visitor language (en/fr/sw/other)")
    language_confidence: float
    language_supported: bool
    intent: str | None = Field(None, description="One item from the fixed intent list, or null when unsure")
    confidence: float = Field(..., ge=0.0, le=1.0)
    ranked: list[Ranked] = Field(default_factory=list, description="Full probability list so the choice is inspectable")
    reply_for_visitor: str | None = Field(None, description="Fixed template rendered in the visitor's language")
    reply_for_operator: str | None = Field(None, description="Same template in Noor's language so she knows what she is sending")
    operator_summary: str = Field(..., description="One line for Noor: what the visitor wants")
    holding_reply: str = Field(..., description="Safe fallback reply, always available")
    model_name: str
    model_version: str


# --------------------------------------------------------------------------- feedback
class FeedbackRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str | None = Field(None, description="Optional; auto-detected when omitted")
    source: str = Field("app", description="app | sms | paste")
    visitor_contact: str | None = None
    client_id: str | None = None


class ClauseAnalysis(BaseModel):
    text: str
    aspect: str | None
    aspect_confidence: float
    aspect_decision: Decision
    sentiment: str | None
    sentiment_confidence: float
    sentiment_decision: Decision


class FeedbackAnalysis(BaseModel):
    id: str
    language: str
    clauses: list[ClauseAnalysis]
    n_confident: int
    n_unsure: int
    model_name: str
    model_version: str


class AspectSummary(BaseModel):
    aspect: str
    positive: int
    negative: int
    examples_positive: list[str]
    examples_negative: list[str]


class FeedbackSummary(BaseModel):
    n_reviews: int
    n_clauses: int
    n_confident: int
    n_unsure: int
    keep_doing: list[AspectSummary] = Field(..., description="Aspects visitors keep praising")
    fix_next: list[AspectSummary] = Field(..., description="Aspects visitors wish were different")
    aspects: list[AspectSummary]


# --------------------------------------------------------------------------- bookings
BookingStatus = Literal["pending", "confirmed", "cancelled", "completed"]


class BookingIn(BaseModel):
    id: str | None = None
    visitor_name: str = ""
    visitor_contact: str = ""
    language: str = "en"
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    time: str = "09:00"
    party_size: int = Field(2, ge=1, le=50)
    status: BookingStatus = "pending"
    notes: str = ""
    source: str = "app"
    enquiry_id: str | None = None


class Booking(BookingIn):
    id: str
    created_at: str
    updated_at: str


class BookingPatch(BaseModel):
    status: BookingStatus | None = None
    date: str | None = None
    time: str | None = None
    party_size: int | None = Field(None, ge=1, le=50)
    notes: str | None = None


# --------------------------------------------------------------------------- profile
class Profile(BaseModel):
    farm_name: str = "Noor's Coffee Farm"
    operator_name: str = "Noor"
    village: str = "Ondera highlands"
    phone: str = "+000 000 000"
    languages: str = "Kiswahili, English (via guide), French (via guide)"
    price_adult: str = "15"
    price_child: str = "5"
    currency: str = "USD"
    duration: str = "2.5 hours"
    includes: str = "farm walk, coffee picking (in season), roasting demonstration, tasting, tea on arrival"
    open_days: str = "Tuesday to Sunday"
    start_times: str = "9:00 and 14:00"
    location_hint: str = "Ondera Coffee Cooperative road, 20 minutes from the district town"
    directions_hint: str = "Turn left at the cooperative sign and follow the murram road uphill for 3 km"
    dietary_note: str = "Vegetarian lunch is available on request. The walk is on uneven paths with some steep sections."
    max_party: int = 12


# --------------------------------------------------------------------------- sync
class QueuedRecord(BaseModel):
    """A record captured offline on the device and forwarded later."""

    id: str
    kind: Literal["enquiry", "booking", "feedback", "profile"]
    payload: dict
    captured_at: datetime
    language: str = "sw"


class SyncRequest(BaseModel):
    client_id: str
    records: list[QueuedRecord]


class SyncResponse(BaseModel):
    accepted: list[str]
    rejected: dict[str, str] = Field(default_factory=dict, description="record id -> reason")


# --------------------------------------------------------------------------- SMS
class SmsInbound(BaseModel):
    """Normalised inbound SMS. Africa's Talking posts form fields `from`, `to`, `text`; Twilio posts `From`, `To`, `Body`."""

    sender: str = Field(..., alias="from")
    text: str
    to: str | None = None

    model_config = {"populate_by_name": True}


class SmsMessage(BaseModel):
    id: int
    created_at: str
    direction: Literal["in", "out"]
    counterpart: str
    text: str
    language: str
    purpose: str


# --------------------------------------------------------------------------- datasets
class Dataset(BaseModel):
    name: str
    kind: Literal["problem_evidence", "build_data", "benchmark"]
    what_it_is: str
    why_it_matters: str
    how_we_use_it: str
    license: str = "check terms"
    size: str = ""
    url: str = ""
    coverage_gaps: str = Field("", description="What this data does NOT cover. Judges score this.")
