"""Завантажує моделі в кеш під час збірки Docker-образу (щоб старт був швидким)."""
from transformers import pipeline

from emotion_engine import EMOTION_MODEL, UK_EN_MODEL

pipeline("translation", model=UK_EN_MODEL)
pipeline("text-classification", model=EMOTION_MODEL, top_k=None)
print("Моделі завантажено.")
