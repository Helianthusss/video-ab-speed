"""Compatibility entry point: python app.py or gunicorn app:app."""

from video_ab.web import app, main

if __name__ == "__main__":
    main()
