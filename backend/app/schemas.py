"""Pydantic models shared by the API routers."""
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Sector(str, Enum):
    tourism = "tourism"


class Decision(str, Enum):
    """Human-in-the-loop outcome. The tool informs; a person decides."""

    answer = "answer"  # confident enough to show a suggestion
    ask_a_person = "ask_a_person"  # "not sure, ask a person"


class InferenceRequest(BaseModel):
    sector: Sector
    text: str = Field(..., min_length=1, max_length=2000, description="User input (text or transcribed voice)")
    language: str = Field("hi", min_length=2, max_length=8, description="ISO 639-1 code of the input language")
    client_id: str | None = Field(None, description="Opaque device/user id for store-and-forward dedupe")


class InferenceResponse(BaseModel):
    decision: Decision
    label: str | None = Field(None, description="One item from the model's fixed list of answers")
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    language: str
    model_name: str
    model_version: str
    sources: list[str] = Field(default_factory=list, description="Datasets / evidence the answer rests on")


class QueuedRecord(BaseModel):
    """A record captured offline on the device and forwarded later."""

    id: str
    sector: Sector
    payload: dict
    captured_at: datetime
    language: str = "hi"


class SyncRequest(BaseModel):
    client_id: str
    records: list[QueuedRecord]


class SyncResponse(BaseModel):
    accepted: list[str]
    rejected: dict[str, str] = Field(default_factory=dict, description="record id -> reason")


class Dataset(BaseModel):
    name: str
    sector: Literal["common", "tourism"]
    what_it_is: str
    why_it_matters: str
    license: str = "check terms"
    coverage_gaps: str = Field("", description="What this data does NOT cover. Judges score this.")
