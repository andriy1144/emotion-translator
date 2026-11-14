---
title: AI Emotion Translator
emoji: 🎭
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# 🎭 AI-перекладач емоцій

Веб-застосунок на **Flask** з інтеграцією ML-моделей **Hugging Face Transformers**.
Користувач вводить текст (українською або англійською) → ШІ визначає емоцію
(радість, сум, гнів, страх, подив, огида, спокій) → застосунок показує емодзі, розподіл
ймовірностей, пораду та підбадьорливу цитату.

Практична робота №9 з дисципліни «Основні принципи роботи та можливості ШІ».

## Як це працює

```
Текст ──► (якщо кирилиця) Helsinki-NLP/opus-mt-uk-en ──► англ. текст
                                                           │
                         j-hartmann/emotion-english-distilroberta-base
                                                           │
                              7 емоцій + ймовірності ──► емодзі, порада, цитата
```

| Модель | Призначення |
|--------|-------------|
| `Helsinki-NLP/opus-mt-uk-en` | переклад українського тексту англійською |
| `j-hartmann/emotion-english-distilroberta-base` | класифікація 7 емоцій |

## Структура

```
app.py               # Flask: сторінка, /api/analyze, /health
emotion_engine.py    # HFEngine (ML) та LexiconEngine (резервний режим)
advice.py            # назви емоцій, емодзі, поради, цитати
templates/index.html # інтерфейс
static/              # style.css, app.js
tests/test_app.py    # pytest
Dockerfile           # для Hugging Face Spaces
requirements.txt     # повний набір (з torch/transformers)
requirements-lite.txt# мінімальний набір (без ML)
```

## Запуск локально

Потрібен Python 3.10+.

**Повний режим (з ML-моделями, перший запуск завантажить ~1 ГБ):**
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Легкий режим (без torch, резервний словниковий аналізатор):**
```bash
pip install -r requirements-lite.txt
EMOTION_ENGINE=lexicon python app.py     # Windows PowerShell: $env:EMOTION_ENGINE="lexicon"; python app.py
```

Відкрийте http://localhost:5000

Змінна `EMOTION_ENGINE`: `auto` (за замовчуванням: ML, а якщо недоступний — резервний), `hf`, `lexicon`.
Поточний рушій видно внизу сторінки та за адресою `/health`.

## API

`POST /api/analyze` з тілом `{"text": "Я щасливий!"}` повертає JSON:
`emotion`, `label`, `emoji`, `confidence`, `headline`, `advice`, `quote`, `translated_text`, `engine`, `scores[]`.
Помилки: `400` (порожній/занадто довгий текст, некоректний JSON), `500` (збій моделі).

## Тести

```bash
pip install pytest
python -m pytest -q tests
```

## Публікація (Hugging Face Spaces)

1. Створіть Space на https://huggingface.co/new-space → SDK **Docker** → Blank.
2. Завантажте файли проєкту в репозиторій Space (через `git push`).
3. Дочекайтесь збірки (кілька хвилин) — застосунок буде доступний за адресою Space.

**Посилання на застосунок:** https://huggingface.co/spaces/<ваш-логін>/<назва-space>

> Навчальний прототип. Результати аналізу не є медичною або психологічною порадою.
