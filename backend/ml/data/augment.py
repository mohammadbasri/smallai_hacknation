"""Template augmentation for the review models (TRAINING ONLY, never in the hold-out set).

Generates short clauses of the form "the <noun> was <adjective>" in en/fr/sw, where each noun maps to one aspect
and each adjective carries a polarity. Negated forms ("the lunch was not good") flip the polarity so the model
sees the bigram "not_good" as negative. This is synthetic data and is declared as such in docs/MODEL_CARD.md.
"""
from __future__ import annotations

import random

# noun -> aspect, per language
NOUNS: dict[str, dict[str, str]] = {
    "en": {
        "coffee": "coffee_tasting", "tasting": "coffee_tasting", "roast": "coffee_tasting", "cupping": "coffee_tasting",
        "walk": "farm_walk", "trail": "farm_walk", "hike": "farm_walk", "farm tour": "farm_walk", "fields": "farm_walk",
        "lunch": "food", "meal": "food", "food": "food", "snacks": "food",
        "guide": "guide_translation", "interpreter": "guide_translation", "translation": "guide_translation", "explanations": "guide_translation",
        "price": "price_value", "cost": "price_value", "fee": "price_value", "value": "price_value",
        "road": "access_road", "directions": "access_road", "drive": "access_road", "location": "access_road",
        "hosts": "hospitality", "welcome": "hospitality", "family": "hospitality", "hospitality": "hospitality",
        "booking": "booking_communication", "reply": "booking_communication", "confirmation": "booking_communication", "communication": "booking_communication",
    },
    "fr": {
        "café": "coffee_tasting", "dégustation": "coffee_tasting", "torréfaction": "coffee_tasting",
        "balade": "farm_walk", "sentier": "farm_walk", "visite de la plantation": "farm_walk", "marche": "farm_walk",
        "déjeuner": "food", "repas": "food", "nourriture": "food",
        "guide": "guide_translation", "interprète": "guide_translation", "traduction": "guide_translation",
        "prix": "price_value", "tarif": "price_value", "coût": "price_value",
        "route": "access_road", "piste": "access_road", "trajet": "access_road", "emplacement": "access_road",
        "accueil": "hospitality", "hôtes": "hospitality", "famille": "hospitality",
        "réservation": "booking_communication", "réponse": "booking_communication", "confirmation": "booking_communication", "communication": "booking_communication",
    },
    "sw": {
        "kahawa": "coffee_tasting", "kuonja": "coffee_tasting", "ukaangaji": "coffee_tasting",
        "matembezi": "farm_walk", "njia": "farm_walk", "ziara ya shamba": "farm_walk",
        "chakula": "food", "chakula cha mchana": "food", "mlo": "food",
        "mwongozaji": "guide_translation", "mkalimani": "guide_translation", "tafsiri": "guide_translation", "maelezo": "guide_translation",
        "bei": "price_value", "gharama": "price_value", "ada": "price_value",
        "barabara": "access_road", "maelekezo": "access_road", "safari": "access_road", "eneo": "access_road",
        "mapokezi": "hospitality", "wenyeji": "hospitality", "familia": "hospitality", "ukarimu": "hospitality",
        "uhifadhi": "booking_communication", "jibu": "booking_communication", "uthibitisho": "booking_communication", "mawasiliano": "booking_communication",
    },
}

ADJ: dict[str, dict[str, list[str]]] = {
    "en": {
        "positive": ["wonderful", "excellent", "great", "lovely", "amazing", "delicious", "friendly", "helpful", "clear",
                     "easy", "fair", "generous", "warm", "beautiful", "perfect", "superb", "fantastic", "smooth", "quick",
                     "well organised", "very good", "brilliant", "pleasant", "reasonable", "welcoming"],
        "negative": ["disappointing", "terrible", "cold", "rushed", "late", "rude", "confusing", "expensive", "muddy",
                     "poor", "bad", "slow", "dirty", "boring", "overpriced", "unclear", "awful", "too long", "too short",
                     "unfriendly", "disorganised", "hard to find", "lukewarm", "not worth it", "a mess"],
    },
    "fr": {
        "positive": ["merveilleux", "excellent", "génial", "charmant", "incroyable", "délicieux", "sympathique", "utile",
                     "clair", "facile", "juste", "généreux", "chaleureux", "magnifique", "parfait", "superbe", "fantastique",
                     "rapide", "bien organisé", "très bon", "agréable", "raisonnable", "accueillant"],
        "negative": ["décevant", "terrible", "froid", "précipité", "en retard", "impoli", "confus", "cher", "boueux",
                     "médiocre", "mauvais", "lent", "sale", "ennuyeux", "trop cher", "flou", "affreux", "trop long",
                     "trop court", "désagréable", "désorganisé", "difficile à trouver", "tiède", "nul"],
    },
    "sw": {
        "positive": ["nzuri sana", "bora", "ya ajabu", "tamu", "ya kirafiki", "ya msaada", "wazi", "rahisi", "ya haki",
                     "ya ukarimu", "ya joto", "ya kupendeza", "kamili", "ya haraka", "iliyopangwa vizuri", "nzuri kabisa",
                     "ya kuvutia", "nafuu", "ya kukaribisha"],
        "negative": ["ya kukatisha tamaa", "mbaya", "baridi", "ya haraka haraka", "imechelewa", "ya kukosa adabu",
                     "ya kuchanganya", "ghali", "yenye matope", "duni", "polepole", "chafu", "ya kuchosha", "ghali mno",
                     "isiyo wazi", "ndefu mno", "fupi mno", "isiyo ya kirafiki", "isiyopangwa", "ngumu kupata", "vuguvugu"],
    },
}

TEMPLATES: dict[str, list[str]] = {
    "en": ["the {noun} was {adj}", "{adj} {noun}", "the {noun} was really {adj}", "{noun}: {adj}", "a {adj} {noun}",
           "we found the {noun} {adj}", "honestly the {noun} was {adj}"],
    "fr": ["le {noun} était {adj}", "la {noun} était {adj}", "{noun} {adj}", "le {noun} était vraiment {adj}",
           "{noun} : {adj}", "nous avons trouvé le {noun} {adj}"],
    "sw": ["{noun} ilikuwa {adj}", "{noun} {adj}", "{noun} ilikuwa {adj} kweli", "{noun}: {adj}", "tuliona {noun} {adj}"],
}

NEGATION: dict[str, list[str]] = {
    "en": ["the {noun} was not {adj}", "the {noun} wasn't {adj} at all", "not a {adj} {noun}"],
    "fr": ["le {noun} n'était pas {adj}", "la {noun} n'était pas du tout {adj}"],
    "sw": ["{noun} haikuwa {adj}", "{noun} haikuwa {adj} hata kidogo"],
}


def generate(per_language: int = 260, seed: int = 7) -> list[tuple[str, str, str, str]]:
    """Returns rows (text, lang, aspect, polarity)."""
    rng = random.Random(seed)
    rows: list[tuple[str, str, str, str]] = []
    for lang, nouns in NOUNS.items():
        noun_items = list(nouns.items())
        seen = set()
        tries = 0
        while len([r for r in rows if r[1] == lang]) < per_language and tries < per_language * 20:
            tries += 1
            noun, aspect = rng.choice(noun_items)
            if rng.random() < 0.2:
                pol = rng.choice(["positive", "negative"])
                adj = rng.choice(ADJ[lang][pol])
                text = rng.choice(NEGATION[lang]).format(noun=noun, adj=adj)
                pol = "negative" if pol == "positive" else "positive"
            else:
                pol = rng.choice(["positive", "negative"])
                adj = rng.choice(ADJ[lang][pol])
                text = rng.choice(TEMPLATES[lang]).format(noun=noun, adj=adj)
            if text in seen:
                continue
            seen.add(text)
            rows.append((text, lang, aspect, pol))
    return rows
