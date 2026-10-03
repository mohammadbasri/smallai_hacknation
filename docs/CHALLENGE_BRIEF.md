# Challenge brief (distilled from file.pdf)

**Small AI for Development Hackathon** · Hack-Nation × World Bank Group Youth Summit · Global AI & Digital Summit, Seoul, October 2026.
Guiding question: *What does localizing AI development mean for you?*

## Key dates

- Competition weekend: 3–4 October 2026
- Shortlist by expert evaluators: 5–6 October
- Ignite Talk by winners in Seoul: 21 October 2026
- One winner per sector (3 total); one representative per team travels.

## Persona: Noor

38, farms 2 ha in the Ondera highlands (coffee upper slope, maize and beans below). Member of the Ondera Coffee Cooperative.
Speaks a local language at home, the national one when needed. Owns a basic phone (calls, SMS, mobile money); borrows
her daughter's smartphone on weekends. No Wi-Fi; buys 3G bundles. Phone stays at the house while she is on the slope.

## Sectors (pick ONE)

| Sector | Noor's problem | Challenge |
| --- | --- | --- |
| **Health** (Annex A) | Overcrowded clinic, outdated guidance, heavy record-keeping | Improve one part of primary-care access or a frontline worker's ability to serve her: screening support, documentation, referral, follow-up, continuity of care. **No medical imaging / diagnosis datasets; interpreting them is out of bounds.** |
| **Agriculture** (Annex B) | Coffee yields dropping, unknown cause; extension officer visits twice a year; buyer names the price | Help her make, communicate or act on one better decision: crop/post-harvest problem ID, timing an activity, localized advisory, documenting a field observation, quality/value addition, pricing/market/extension next step. |
| **Tourism** (Annex C) | 6–7 visitors/month by word of mouth; language barrier; no idea what worked | Complete one business workflow: becoming discoverable, cross-language communication, responding to enquiries, shaping an experience, managing a booking, learning from feedback, following up. |

## The rules (all must hold)

1. Runs on a device the user already has.
2. Core feature works **offline**.
3. Model files are small enough to side-load or send over a weak connection.
4. At least one interaction is in a **local language** (voice or text). Name the language; expect to be asked how it fares in a less-supported one.

### AI guardrails (pass/fail)

- **Human in the loop**: a person makes the final call. The tool informs and flags uncertainty; it does not act for the user. Agentic flows must check in appropriately.
- **Avoid hallucinations**: when data is insufficient, say "not sure, ask a person" rather than guess.
- Prefer a **fixed list of answers** so output can be checked for safety.
- Health entries: state where patient data sits, who can read it, what happens when the phone is lost or shared.

## Judging

| Criterion | Weight |
| --- | --- |
| Built solution (Small AI fidelity, works end to end within sector constraints) | 25% |
| Development relevance and impact | 20% |
| Data grounding (addresses an identified data gap; sound modeling) | 15% |
| Evidence it works | 15% |
| Clarity, design, inclusivity + value proposition for AI (why not SMS / spreadsheet / search?) | 15% |
| Scalability, replicability, what happens next | 10% |
| Responsible AI, data and safety | Pass/fail |

## Deliverables (by end of 4 October)

1. **Prototype**: the working tool, with code or a link.
2. **Video, 2–5 min** (required for shortlist):
   - Problem statement, one sentence: *Because of this tool, [user] will [action] by [when] that they would otherwise [not do / do late / do worse]; we know because [evidence].*
   - AI capabilities and why a simpler tool would not do the job; mention guardrails.
   - Tool demo: end-to-end user journey (slides or screen recording).
   - The gap being addressed: where the tool sits in the user's day; tech stack for technical builds.
   - Your take on what localizing AI development means.

## Data (two layers, cite both)

1. **Data that shows the problem**: cite source, year, country. Flag synthetic figures.
2. **Data you build with**: name every dataset, source, license, size. **State what the data does not cover; this is scored.** Label synthetic data as such.

### Common datasets

- **Language and speech**: Mozilla Common Voice (CC0), FLEURS, MMS (Meta), FLORES-200 / NLLB-200, OPUS, MASSIVE (Amazon), Masakhane, AI4Bharat / IndicVoices.
- **Connectivity, devices, inclusion**: GSMA Mobile Gender Gap Report, OpenCelliD, Global Findex.
- **Maps, population, satellite**: WorldPop, OpenStreetMap, VIIRS Nighttime Lights.
- **Country statistics**: World Bank Data360, World Development Indicators, World Bank Microdata Library / Data Catalog, Humanitarian Data Exchange.

### Health (Annex A)

Service Delivery Indicators (World Bank), healthsites.io, Maina et al. (Scientific Data), DHS Program / Service Provision Assessments, Malaria Atlas Project travel-time surfaces, AccessMod (WHO), DHIS2, WHO Global Health Observatory, Global Health Data Exchange (IHME).

### Agriculture (Annex B)

LSMS-ISA, Cassava Leaf Disease and iBean (Makerere), PlantVillage (studio images; be honest about the gap), PlantDoc (field images), BRACOL (Arabica coffee leaf disease), WFP food prices via HDX, CHIRPS, iSDAsoil / SoilGrids, Digital Earth Africa, Sentinel-2 / Landsat, NASA POWER, FAOSTAT.

### Tourism (Annex C)

UN Tourism statistics, WDI tourism series, World Bank Enterprise Surveys, OpenStreetMap via Overpass, Wikivoyage, Yelp Open Dataset (check license), MASSIVE, FLORES-200 / NLLB-200.

## Glossary (short)

- **Small AI**: targeted, use-case-driven AI on a device the user already has; governed by the operating constraint, not model scale.
- **Store-and-forward**: save now, send later; record waits on the phone until a signal appears.
- **Quantization**: shrinking a model so it fits a basic device or downloads over a weak link.
- **Fixed list of answers**: the complete set of things the tool may say; if it can say anything, it cannot be checked for safety.
- **Low-resource language**: little digital text or recorded speech available, so most AI tools support it poorly.
