"""Build the bundled demo session while the image is being built.

The Space has no persistent disk, so every restart returns to exactly this
state: video imported, lines locked, ready to measure. No measurement records
are included; vehicles are meant to be clicked live during the demonstration.
"""

import sys
from pathlib import Path

from video_ab.media import index_video
from video_ab.services import new_session, validate_session
from video_ab.storage import save

CLIP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "demo.mp4"

# Illustrative positions only. These are not surveyed cross-sections and the
# distance below is not a field measurement.
LINE_A = [[0.167, 0.694], [0.896, 0.546]]
LINE_B = [[0.100, 0.860], [0.950, 0.700]]


def main():
    meta = index_video(CLIP)
    session = new_session("Demo")
    session.update(
        site="DEMO-HF",
        location="Bản trình diễn trực tuyến",
        observer="Bản demo",
        L=100,
        start=0,
        end=120,
        interval_seconds=120,
        videoA=meta["id"],
        videoB=meta["id"],
        lines={"A": LINE_A, "B": LINE_B},
        line_locked={"A": True, "B": True},
    )
    session["sync"].update(
        verified=True,
        anchor_end=120,
        references=["Demo: Camera A và B dùng cùng một video, offset 0 giây"],
    )
    validate_session(session)
    save(session, "seed demo session")
    print("Demo session:", session["id"])
    print("Frames indexed:", len(meta["frames"]))


if __name__ == "__main__":
    main()
