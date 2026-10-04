"""Data sources the entry cites, in the two layers the brief asks for:
problem_evidence (shows the gap is real) and build_data (what the models learned from). Coverage gaps are scored."""
from fastapi import APIRouter

from app.schemas import Dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

DATASETS: list[Dataset] = [
    # ------------------------------------------------------------- problem evidence
    Dataset(
        name="World Bank, Jordan Youth, Technology and Jobs / tourism digitalisation support",
        kind="problem_evidence",
        what_it_is="World Bank-supported work bringing small tourism operators onto digital platforms (listing, booking, payments).",
        why_it_matters="Names the binding constraint for informal operators: no digital listing and no skills to manage one. Our Listing and Inbox features sit exactly there.",
        how_we_use_it="Framing in the video and README; the 'what happens next' argument.",
        license="Public (World Bank project documents)",
        url="https://projects.worldbank.org/",
        coverage_gaps="Jordan, not East Africa; urban-adjacent operators. We assume the constraint transfers to a highland coffee farm; that is an assumption, not a measurement.",
    ),
    Dataset(
        name="World Development Indicators: international tourism receipts, arrivals (World Bank)",
        kind="problem_evidence",
        what_it_is="Country indicators for tourism receipts, arrivals and expenditure by year.",
        why_it_matters="Shows how much visitor money matters to the economy Noor lives in.",
        how_we_use_it="Cited in the brief/README for scale; not used in any model.",
        license="CC-BY 4.0",
        url="https://databank.worldbank.org/source/world-development-indicators",
        coverage_gaps="National totals; nothing about informal micro-operators like a farm tour, which are invisible in receipts data.",
    ),
    Dataset(
        name="World Bank Enterprise Surveys",
        kind="problem_evidence",
        what_it_is="Firm-level surveys across 150+ economies including the smallest firms: finance, skills, informality constraints.",
        why_it_matters="Evidence on what actually constrains a small operator.",
        how_we_use_it="Framing only.",
        license="Free registration",
        url="https://www.enterprisesurveys.org/",
        coverage_gaps="Formal registered firms are over-represented; a household farm offering tours is at the edge of the sampling frame.",
    ),
    Dataset(
        name="GSMA Mobile Gender Gap Report",
        kind="problem_evidence",
        what_it_is="Phone and smartphone ownership by gender and country.",
        why_it_matters="Evidence for the device Noor actually has: a basic phone, with a smartphone only sometimes. This drove the SMS channel.",
        how_we_use_it="Design constraint (D-004): the core channel is SMS, the PWA is for the weekend smartphone.",
        license="Free report",
        url="https://www.gsma.com/r/gender-gap/",
        coverage_gaps="Country-level; rural highland women specifically are not broken out.",
    ),
    # ------------------------------------------------------------- build data
    Dataset(
        name="Karibu synthetic seed corpus (this repo, backend/ml/data)",
        kind="build_data",
        what_it_is="Hand-written enquiry patterns (en/fr/sw, 9 intents, slot-filled) and review clauses (9 aspects, 2 polarities) plus noun+adjective template augmentation.",
        why_it_matters="It is what all four shipped models were trained on. Small enough to read in full and audit.",
        how_we_use_it="Training data for intent, langid, aspect and sentiment models. Hold-out metrics in shared/models/METRICS.md.",
        license="MIT (this repository)",
        size="~1,060 enquiry sentences from ~290 patterns; ~480 hand-written clauses; ~780 augmented clauses",
        coverage_gaps="SYNTHETIC. Not real visitor traffic. No code-switching (Swahili-English mixing is common in practice), no typos or SMS shorthand, no emoji, no WhatsApp voice notes. Swahili was written by the team, not sampled from native speakers' messages. German/Spanish/Italian/Portuguese appear only as 'unsupported language' negatives.",
    ),
    Dataset(
        name="MASSIVE (Amazon)",
        kind="build_data",
        what_it_is="~1M short utterances in 51 languages labelled by intent (smart-assistant domain), incl. Swahili and French.",
        why_it_matters="The closest open template for sorting requests into a fixed intent list; it shaped our intent taxonomy and the slot-filling pattern style.",
        how_we_use_it="Design reference now; the training script can ingest MASSIVE utterances as extra 'other' class negatives (planned).",
        license="CC-BY 4.0",
        url="https://github.com/alexa/massive",
        coverage_gaps="Assistant commands (alarms, weather), not tourism; intents do not map 1:1 onto ours.",
    ),
    Dataset(
        name="Yelp Open Dataset",
        kind="build_data",
        what_it_is="Millions of real business reviews released for academic use.",
        why_it_matters="Real review language for the 'what did visitors actually like' task. Our sentiment model is the weakest (0.69 hold-out); this is the data that would fix it.",
        how_we_use_it="Style reference for the synthetic clauses. Planned: fine-tune the sentiment model on Yelp polarity, English only.",
        license="Yelp dataset licence (academic, non-commercial); check before any commercial use",
        url="https://www.yelp.com/dataset",
        coverage_gaps="North-American, English, restaurants/services; no Swahili or French; no farm tours.",
    ),
    Dataset(
        name="Wikivoyage",
        kind="build_data",
        what_it_is="Openly licensed travel guide text in many languages.",
        why_it_matters="Multilingual tourism vocabulary for what visitors ask about.",
        how_we_use_it="Vocabulary reference when writing fr/sw patterns.",
        license="CC-BY-SA 3.0",
        url="https://www.wikivoyage.org/",
        coverage_gaps="Guide prose, not visitor messages; Swahili edition is small.",
    ),
    Dataset(
        name="FLORES-200 / NLLB-200 (Meta)",
        kind="benchmark",
        what_it_is="Translation benchmark and open models across 200 languages including Swahili.",
        why_it_matters="The brief's suggested path for 'the message arrives in a language Noor cannot read'.",
        how_we_use_it="NOT used at runtime: NLLB-200-distilled-600M is ~1.2 GB, too large to side-load over 3G. We use fixed pre-translated templates instead (D-009) and name NLLB as the edge-box upgrade path.",
        license="CC-BY-SA 4.0 (data) / CC-BY-NC 4.0 (models)",
        url="https://github.com/facebookresearch/flores",
        coverage_gaps="Formal register; informal chat and code-switching are weaker.",
    ),
    Dataset(
        name="Mozilla Common Voice (Swahili)",
        kind="benchmark",
        what_it_is="Crowdsourced CC0 voice recordings; Swahili has several hundred validated hours.",
        why_it_matters="The path to a voice interaction for Noor (F-17).",
        how_we_use_it="Not used yet. Named as the data for a Swahili speech front-end on the edge box.",
        license="CC0",
        url="https://commonvoice.mozilla.org/",
        coverage_gaps="Read speech, not conversational; accents vary by contributor pool.",
    ),
    Dataset(
        name="OpenStreetMap via Overpass",
        kind="problem_evidence",
        what_it_is="Open map data: accommodation, attractions, roads, points of interest.",
        why_it_matters="The findability baseline: what a visitor searching near Ondera would and would not discover today.",
        how_we_use_it="Framing for the Listing feature; offline base-map idea for directions (planned).",
        license="ODbL",
        url="https://overpass-turbo.eu/",
        coverage_gaps="Rural POI coverage is sparse exactly where Noor is; absence on the map is the point, but it also means we cannot validate the directions template against map data.",
    ),
]


@router.get("", response_model=list[Dataset])
def list_datasets(kind: str | None = None):
    if kind:
        return [d for d in DATASETS if d.kind == kind]
    return DATASETS
