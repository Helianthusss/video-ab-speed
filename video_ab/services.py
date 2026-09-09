"""Session creation and measurement workflow validation."""

import uuid

from .media import metadata
from .storage import now


def new_session(mode):
    if mode not in ["Demo", "Research"]:
        raise ValueError("Chế độ không hợp lệ")
    return dict(
        id=str(uuid.uuid4()),
        mode=mode,
        project="Pedestrian safety",
        site="",
        location="",
        observer="",
        session_start="",
        timezone="Asia/Ho_Chi_Minh",
        reference="A",
        L=None,
        uL=None,
        uT=None,
        start=0,
        end=900,
        interval_seconds=900,
        videoA=None,
        videoB=None,
        setup={},
        site_changes=[],
        events=[],
        records=[],
        flow=[],
        plans=[],
        audits=[],
        lines={"A": None, "B": None},
        line_locked={"A": False, "B": False},
        sync={
            "verified": False,
            "offset_start": 0,
            "offset_end": 0,
            "anchor_start": 0,
            "anchor_end": 900,
            "references": [],
            "version": 1,
            "convention": "tB corrected=tB raw+offset(tB raw); A reference",
        },
        protocol={
            "version": "V4-implementation-1",
            "locked": False,
            "estimand": "prevailing segment travel speed",
            "sampling": "census",
            "pilot_speed": [10, 80],
            "warning_speed": [1, 160],
            "bootstrap": 1000,
            "seed": 20260906,
            "iid_ci": False,
            "allow_percentile": True,
            "qc_rules": "Quyết định giữ/loại thủ công; phải ghi lý do và người duyệt",
            "percentile": "Hyndman-Fan type 7 / numpy linear",
            "audit_fraction": 0.1,
        },
        created=now(),
    )


def validate_session(s):
    if s["end"] <= s["start"] or s["interval_seconds"] <= 0:
        raise ValueError("Khoảng thời gian không hợp lệ")
    sy = s["sync"]
    if sy["anchor_end"] <= sy["anchor_start"]:
        raise ValueError("Mốc đồng bộ cuối phải sau mốc đầu")
    if 1 + (sy["offset_end"] - sy["offset_start"]) / (sy["anchor_end"] - sy["anchor_start"]) <= 0:
        raise ValueError("Drift làm đảo thứ tự thời gian")
    if s["L"] is not None and s["L"] <= 0:
        raise ValueError("L phải dương")
    p = s["protocol"]
    if not 100 <= p["bootstrap"] <= 10000:
        raise ValueError("Bootstrap 100–10000 lần")
    if not 0 < p["pilot_speed"][0] < p["pilot_speed"][1]:
        raise ValueError("Khoảng tốc độ pilot không hợp lệ")
    if p["locked"] and (
        not s["site"]
        or not s["observer"]
        or not s["L"]
        or not sy["verified"]
        or not sy["references"]
        or not all(s["line_locked"].values())
    ):
        raise ValueError("Khóa cần site, người đo, L, mốc đồng bộ và hai vạch đã khóa")


def stamp(s, r, cam, index):
    key = s.get("video" + cam)
    if not key:
        raise ValueError("Camera " + cam + " chưa có video")
    m = metadata(key)
    if not isinstance(index, int) or index < 0 or index >= len(m["frames"]):
        raise ValueError("Frame " + cam + " không hợp lệ")
    f = m["frames"][index]
    r["frame" + cam] = index
    r["t" + cam] = f["time"]
    r["pts" + cam] = f["pts"]
    r["time_base" + cam] = f["time_base"]
    r["video" + cam] = m["id"]


def measurement_readiness(s):
    missing = []
    if not s.get("videoA") or not s.get("videoB"):
        missing.append("nhập đủ video A và B")
    if not s.get("observer"):
        missing.append("nhập tên người thao tác")
    if not s.get("L") or s["L"] <= 0:
        missing.append("nhập khoảng cách L")
    if not s.get("sync", {}).get("verified") or not s.get("sync", {}).get("references"):
        missing.append("xác nhận đồng bộ và căn cứ")
    if not all(s.get("line_locked", {}).get(c) and s.get("lines", {}).get(c) for c in ["A", "B"]):
        missing.append("vẽ và khóa hai vạch A, B")
    return missing
