# Build for Koyeb. The application code and the demo clip both come from this
# repository, so the container needs nothing from the network at run time.
FROM python:3.12-slim

# fonts-dejavu-core: reportlab needs a Unicode font for the Vietnamese PDF export.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
USER app

ENV HOME=/home/app \
    PATH=/home/app/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    AB_DATA_DIR=/home/app/data \
    AB_OUTPUT_DIR=/home/app/outputs

WORKDIR /home/app/src

COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=app:app . .

# Index the PTS table while building so the container serves frames immediately.
RUN python deploy/huggingface/seed_demo.py deploy/huggingface/demo.mp4

# A single worker keeps the SQLite lock and the frame cache in one process.
CMD ["sh", "-c", "gunicorn --workers 1 --threads 4 --timeout 300 --bind 0.0.0.0:${PORT:-8000} video_ab.web:app"]
