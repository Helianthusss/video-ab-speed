# Hugging Face Space, CPU Basic. The demo video and its PTS index are baked into
# the image at build time so the Space starts immediately and always starts clean.
FROM python:3.12-slim

# git: install the application from its repository.
# fonts-dejavu-core: reportlab needs a Unicode font for the Vietnamese PDF export.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    AB_DATA_DIR=/home/user/data \
    AB_OUTPUT_DIR=/home/user/outputs \
    AB_HOST=0.0.0.0 \
    AB_PORT=7860

WORKDIR /home/user/app

RUN pip install --no-cache-dir --user \
    "video-ab-survey @ git+https://github.com/Helianthusss/video-ab-speed.git@main"

COPY --chown=user:user demo.mp4 seed_demo.py ./
RUN python seed_demo.py

EXPOSE 7860

# One worker keeps the SQLite lock and the frame cache inside a single process.
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "300", \
     "--bind", "0.0.0.0:7860", "video_ab.web:app"]
