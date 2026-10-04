# Video script (2–5 minutes) · Karibu

Follow the brief's required order. Timings assume about 3 minutes 30.

## 0:00 Problem statement (one sentence, the brief's format)

> Because of this tool, **Noor** will **understand and answer a visitor's enquiry in the visitor's language, from the phone she already has, the same day** that she would otherwise **answer late, through a guide, or not at all**; we know because **the brief's Tourism scenario describes visitors who need a local guide to translate and an operator who never learns what worked, the GSMA Mobile Gender Gap Report shows the device such women own is most often a basic phone, and the World Bank's work with small operators in Jordan found the binding constraint was the missing digital listing and the skills to manage one.**

Before recording, pull the exact GSMA figure for the demo country (basic vs smartphone ownership, women, rural) and quote it with year.

## 0:25 Who Noor is, in two sentences

Coffee farmer, six or seven visitors a month by word of mouth, a basic phone for calls and SMS, a smartphone only at weekends, 3G bundles, Kiswahili at home. Visitors write in English or French.

## 0:40 AI capabilities, and why not SMS / a spreadsheet / a search

- Four tiny text models (2 MB total) read the message: which language, what the visitor wants, and for feedback, what each sentence is about and whether it is praise or complaint.
- Why a simpler tool does not do this: an SMS can carry the message but cannot read it; a spreadsheet cannot tell "price" from "cancel" in French; a search needs Noor to know what to search for. The AI reads so Noor can decide.
- Guardrails, say them out loud: nothing is sent without Noor; below 65% confidence the tool says "not sure" and suggests nothing; every reply comes from a fixed template list, so it cannot invent a price or a road; confidence is always on screen.

## 1:20 Demo (screen recording), end to end

1. **Inbox (smartphone, airplane mode on).** Paste "Hi! How much is the coffee tour for 2 adults on Saturday?". Show: language English, "Anauliza bei" in Kiswahili, confidence bar, the English reply with the Kiswahili meaning underneath. Press "Copy & mark as sent".
2. **Unsure case.** Paste a German message. Show it is flagged as another language, no guessed reply, the polite "please write in English, French or Kiswahili" note offered.
3. **Nonsense / out of scope.** Paste "Is this the number for the clinic?". Show "not sure, read it yourself".
4. **Bookings.** From a Swahili booking enquiry, tap "Create a booking", confirm it, show the French confirmation message generated from the profile.
5. **Feedback.** Load the six sample reviews, show the clause table with "unsure" rows, then "Keep doing: coffee tasting, hospitality. Fix next: getting there, food." and the "x of y parts were clear enough to count" line.
6. **Basic phone (SMS page).** Visitor texts the farm number; Noor receives one Kiswahili SMS: what they want, reply 1 or 2. Noor replies "1"; the visitor receives the English template. Point out this runs on a small box at the cooperative.
7. Turn airplane mode off: the queued records sync to the box.

## 2:50 The gap and where the tool sits in Noor's day

Morning, phone at the house: SMS notification, reply "1" from the slope. Weekend, daughter's smartphone: paste WhatsApp messages, confirm bookings, read the week's feedback. Tech stack in one line: React PWA + FastAPI + SQLite, models as JSON, one Docker image for a Raspberry Pi or a Hugging Face Space.

## 3:15 Our take: what localising AI development means

Not a bigger model that happens to speak Swahili. A small one shaped by Noor's constraints: her phone, her signal, her language, her right to decide. The AI reads; Noor answers. Say the trade-off honestly: templates instead of translation means Noor cannot yet type a free reply and have it translated; that is the next step, on the edge box, with NLLB.

## 3:35 End card

Repo, model card with hold-out numbers, data sources and their gaps.
