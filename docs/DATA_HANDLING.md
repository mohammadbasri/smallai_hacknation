# Data handling

Where data sits, who can read it, and what happens when the phone is lost or shared.

## What the tool stores

| Data | Where | Why |
| --- | --- | --- |
| Visitor messages (text), optional phone/name | Noor's phone (browser localStorage) and, when a signal is available, the cooperative's edge box / server (SQLite) | To show the inbox and the reply history |
| Bookings (name, contact, date, party size, notes) | same | The booking ledger |
| Visitor feedback text and its clause tags | same | The "keep doing / fix next" summary |
| Farm profile (prices, hours, directions) | same | Fills every reply template |
| SMS log (direction, number, text) | edge box / server only | The basic-phone channel |

Nothing else. No payments, no IDs, no photos, no location tracking of visitors or of Noor.

## Where it does **not** go

- No third-party AI service: all models run on the phone or on the edge box. No message is sent to any API for analysis.
- No training on visitor data: the models are trained offline on synthetic data. Nothing a visitor writes is used to train anything.
- No analytics or tracking scripts in the app.
- If a real SMS gateway (Africa's Talking, Twilio) is configured, message text and numbers transit that provider, as with any SMS.

## Who can read it

- Noor, on her phone.
- Whoever operates the edge box (the cooperative). The SQLite file is readable by anyone with access to that machine; put it on an encrypted disk and limit shell access.
- Visitors see only the messages Noor chooses to send them.

## Lost or shared phone

- The web app has no login. Anyone holding the unlocked phone can see the inbox and bookings. Phone-level lock is the control, as for WhatsApp.
- Clearing the browser's site data removes everything stored locally. Records already synced remain on the edge box.
- Noor's daughter's smartphone is shared: the app stores business messages only, and the SMS channel means Noor's own
  basic phone never holds more than one notification at a time.

## Consent and purpose

- Visitors message a business number to ask about a tour; replying to them is the expected use.
- The feedback summary uses what visitors wrote to the farm. If reviews are copied from a public platform, respect that platform's terms.
- Retention: not automated yet. Recommended: delete handled enquiries and completed bookings after 12 months (planned, F-33).

## Bias and oversight

- The models were trained on team-written text; see [MODEL_CARD.md](MODEL_CARD.md) for coverage gaps.
- A person makes the final call on every message. Below-threshold cases are shown as "not sure" with no suggestion.
