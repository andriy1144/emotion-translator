"""Рушії визначення емоцій.

HFEngine      — реальні ML-моделі Hugging Face Transformers:
                1) Helsinki-NLP/opus-mt-uk-en  (переклад українського тексту англійською)
                2) j-hartmann/emotion-english-distilroberta-base (класифікація 7 емоцій)
LexiconEngine — легкий словниковий резервний режим (без ML-залежностей), щоб
                застосунок запускався навіть без torch/transformers.

Інтерфейс однаковий: engine.predict(text) -> {"scores": {emotion: prob}, "translated": str | None}
"""
import logging
import math
import os
import re

log = logging.getLogger("emotion")

EMOTION_KEYS = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]
UK_EN_MODEL = "Helsinki-NLP/opus-mt-uk-en"
EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
CYRILLIC = re.compile(r"[а-яіїєґ]", re.IGNORECASE)


class HFEngine:
    name = "hf"
    description = f"{EMOTION_MODEL} + {UK_EN_MODEL}"

    def __init__(self, translator=None, classifier=None):
        # translator/classifier можна передати ззовні (використовується в тестах)
        if translator is None or classifier is None:
            from transformers import pipeline  # імпорт тут, щоб lite-режим працював без transformers
            log.info("Завантаження моделей Hugging Face...")
            translator = translator or pipeline("translation", model=UK_EN_MODEL)
            classifier = classifier or pipeline("text-classification", model=EMOTION_MODEL, top_k=None)
            log.info("Моделі завантажено.")
        self.translator = translator
        self.classifier = classifier

    def predict(self, text):
        translated = None
        english = text
        if CYRILLIC.search(text):
            out = self.translator(text, max_length=256)
            translated = out[0]["translation_text"]
            english = translated

        out = self.classifier(english, truncation=True)
        if out and isinstance(out[0], list):  # різні версії transformers повертають різну вкладеність
            out = out[0]
        scores = {k: 0.0 for k in EMOTION_KEYS}
        for item in out:
            label = item["label"].lower()
            if label in scores:
                scores[label] = float(item["score"])
        return {"scores": scores, "translated": translated}


class LexiconEngine:
    name = "lexicon"
    description = "словниковий резервний режим (без ML-моделей)"

    # основи слів (українською та англійською), що шукаються на початку слова
    LEXICON = {
        "joy": ["рад", "щасл", "чудов", "класн", "кайф", "ура", "люблю", "задоволен", "вдал", "перемог",
                "захопл", "весел", "посміх", "дякую", "happy", "great", "love", "glad", "awesome",
                "wonderful", "excited", "joy", "amazing"],
        "sadness": ["сум", "смут", "плач", "плак", "самотн", "шкод", "тужи", "депрес", "нудьг", "втрат",
                    "розчарова", "боляч", "sad", "cry", "lonely", "miss", "depress", "unhappy", "grief"],
        "anger": ["зли", "злю", "гнів", "бісит", "дратує", "дратув", "ненавиджу", "лют", "обурен",
                  "angry", "hate", "furious", "annoy", "mad", "rage"],
        "fear": ["страх", "боюс", "бою", "тривог", "лякає", "лякає", "паніч", "хвилююс", "жах",
                 "afraid", "scare", "fear", "anxious", "anxiety", "panic", "worried", "terrif"],
        "surprise": ["здивов", "вау", "неймовір", "не очікув", "шок", "несподіван", "ого",
                     "wow", "surpris", "unexpected", "unbelievable", "shock"],
        "disgust": ["огид", "гидк", "бридк", "нудить", "неприємн", "відраз",
                    "disgust", "gross", "nasty", "revolting", "yuck"],
    }
    _patterns = {k: [re.compile(r"\b" + re.escape(s)) for s in v] for k, v in LEXICON.items()}

    def predict(self, text):
        low = text.lower()
        raw = {k: 0.0 for k in EMOTION_KEYS}
        for emotion, pats in self._patterns.items():
            raw[emotion] = float(sum(len(p.findall(low)) for p in pats))
        raw["neutral"] = 0.6  # базовий «спокій», якщо слів-маркерів немає
        exp = {k: math.exp(1.6 * v) for k, v in raw.items()}
        total = sum(exp.values())
        return {"scores": {k: v / total for k, v in exp.items()}, "translated": None}


def get_engine():
    """EMOTION_ENGINE: auto (за замовчуванням) | hf | lexicon"""
    mode = os.getenv("EMOTION_ENGINE", "auto").lower()
    if mode == "lexicon":
        return LexiconEngine()
    if mode == "hf":
        return HFEngine()
    try:
        return HFEngine()
    except Exception as exc:  # немає transformers/torch, немає мережі для завантаження тощо
        log.warning("HF-моделі недоступні (%s: %s). Використовую резервний режим.", type(exc).__name__, exc)
        return LexiconEngine()
