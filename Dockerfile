# Образ для публікації на Hugging Face Spaces (SDK: Docker)
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    EMOTION_ENGINE=hf
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .
# моделі завантажуються на етапі збірки й потрапляють у кеш образу
RUN python download_models.py

EXPOSE 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "--timeout", "180", "app:app"]
