import os
import sys

import pytest

os.environ.setdefault("EMOTION_ENGINE", "lexicon")  # щоб імпорт app не завантажував ML-моделі
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import MAX_LEN, create_app  # noqa: E402
from emotion_engine import HFEngine, LexiconEngine  # noqa: E402


@pytest.fixture
def client():
    return create_app(LexiconEngine()).test_client()


def post(client, payload):
    return client.post("/api/analyze", json=payload)


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "перекладач емоцій" in r.get_data(as_text=True).lower()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok", "engine": "lexicon"}


@pytest.mark.parametrize("text,expected", [
    ("Я дуже щасливий, сьогодні чудовий день!", "joy"),
    ("Мені так сумно і самотньо...", "sadness"),
    ("Мене це страшенно бісить, я ненавиджу таке", "anger"),
    ("Я боюся завтрашнього іспиту, мене охоплює паніка", "fear"),
    ("Вау, це неймовірно, я в шоці!", "surprise"),
    ("Це так гидко і огидно", "disgust"),
    ("Сьогодні вівторок, я йду до університету", "neutral"),
    ("I am so happy and excited today", "joy"),
])
def test_lexicon_emotions(client, text, expected):
    r = post(client, {"text": text})
    assert r.status_code == 200
    data = r.get_json()
    assert data["emotion"] == expected
    assert data["emoji"] and data["advice"] and data["quote"]
    assert len(data["scores"]) == 7
    assert abs(sum(s["score"] for s in data["scores"]) - 1) < 0.01


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": "   "}, {"text": 123}, [], "рядок"])
def test_invalid_input(client, payload):
    r = post(client, payload)
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_text_too_long(client):
    assert post(client, {"text": "а" * (MAX_LEN + 1)}).status_code == 400


def test_not_json(client):
    assert client.post("/api/analyze", data="abc").status_code == 400


def test_unknown_route_and_method(client):
    assert client.get("/nope").status_code == 404
    assert client.get("/api/analyze").status_code == 405


def test_engine_failure_returns_500():
    class Broken:
        name, description = "broken", "x"

        def predict(self, text):
            raise RuntimeError("boom")

    r = post(create_app(Broken()).test_client(), {"text": "привіт"})
    assert r.status_code == 500 and "error" in r.get_json()


# ---- HFEngine з підставними (fake) pipeline: перевіряємо логіку без завантаження моделей ----
def fake_classifier(nested):
    def _c(text, **kw):
        scores = [{"label": "joy", "score": 0.9}, {"label": "sadness", "score": 0.05},
                  {"label": "neutral", "score": 0.05}]
        return [scores] if nested else scores
    return _c


@pytest.mark.parametrize("nested", [True, False])
def test_hf_engine_translates_ukrainian(nested):
    calls = []

    def translator(text, **kw):
        calls.append(text)
        return [{"translation_text": "I am happy"}]

    eng = HFEngine(translator=translator, classifier=fake_classifier(nested))
    res = eng.predict("Я щасливий")
    assert calls == ["Я щасливий"]
    assert res["translated"] == "I am happy"
    assert res["scores"]["joy"] == 0.9 and res["scores"]["anger"] == 0.0


def test_hf_engine_skips_translation_for_english():
    def translator(text, **kw):
        raise AssertionError("не повинен викликатись")

    eng = HFEngine(translator=translator, classifier=fake_classifier(False))
    assert eng.predict("I am happy")["translated"] is None
