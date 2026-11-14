"""Flask-застосунок «AI-перекладач емоцій»."""
import logging
import os
import random

from flask import Flask, jsonify, render_template, request

from advice import ADVICE, EMOTIONS
from emotion_engine import get_engine

MAX_LEN = 500
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("app")


def create_app(engine=None):
    app = Flask(__name__)
    app.config["ENGINE"] = engine or get_engine()
    log.info("Рушій: %s", app.config["ENGINE"].name)

    @app.get("/")
    def index():
        eng = app.config["ENGINE"]
        return render_template("index.html", max_len=MAX_LEN, engine_name=eng.name,
                               engine_desc=eng.description)

    @app.get("/health")
    def health():
        return jsonify(status="ok", engine=app.config["ENGINE"].name)

    @app.post("/api/analyze")
    def analyze():
        data = request.get_json(silent=True)
        text = data.get("text") if isinstance(data, dict) else None
        if not isinstance(text, str) or not text.strip():
            return jsonify(error="Введіть текст для аналізу."), 400
        text = text.strip()
        if len(text) > MAX_LEN:
            return jsonify(error=f"Текст занадто довгий (максимум {MAX_LEN} символів)."), 400

        engine = app.config["ENGINE"]
        try:
            result = engine.predict(text)
        except Exception:
            log.exception("Помилка під час аналізу тексту")
            return jsonify(error="Не вдалося проаналізувати текст. Спробуйте ще раз."), 500

        scores = sorted(result["scores"].items(), key=lambda kv: kv[1], reverse=True)
        top, top_score = scores[0]
        info, tips = EMOTIONS[top], ADVICE[top]
        return jsonify(
            emotion=top,
            label=info["label"],
            emoji=info["emoji"],
            confidence=round(top_score, 4),
            headline=tips["headline"],
            advice=tips["advice"],
            quote=random.choice(tips["quotes"]),
            translated_text=result.get("translated"),
            engine=engine.name,
            scores=[{"emotion": k, "label": EMOTIONS[k]["label"], "emoji": EMOTIONS[k]["emoji"],
                     "score": round(v, 4)} for k, v in scores],
        )

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Не знайдено."), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return jsonify(error="Метод не дозволений."), 405

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
