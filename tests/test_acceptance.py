"""Acceptance tests; all runtime writes stay in a temporary directory."""

import copy
import math
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

_temporary = tempfile.TemporaryDirectory(prefix="video-ab-tests-")
_root = Path(_temporary.name)
_keys = ("AB_DATA_DIR", "AB_OUTPUT_DIR", "AB_DEMO_DIR", "AB_USERNAME", "AB_PASSWORD")
_previous = {key: os.environ.get(key) for key in _keys}
os.environ.update(
    AB_DATA_DIR=str(_root / "data"),
    AB_OUTPUT_DIR=str(_root / "outputs"),
    AB_DEMO_DIR=str(_root / "demo"),
    AB_USERNAME="",
    AB_PASSWORD="",
)

from video_ab.config import DATA_DIR, DEMO_DIR, OUTPUT_DIR
from video_ab.core import agreement, corrected, measure, plan, stats, summary
from video_ab.media import frame_bytes, index_video, metadata
from video_ab.services import measurement_readiness
from video_ab.storage import db, get, save
from video_ab.web import app


def setUpModule():
    subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "scripts.demo_build"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def tearDownModule():
    for key, value in _previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    _temporary.cleanup()


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.s = get((DEMO_DIR / "synthetic_session_id.txt").read_text())
        self.r = copy.deepcopy(self.s["records"][0])
        self.c = app.test_client()

    def test_speed_100(self):
        self.assertEqual(measure(self.r, self.s)["speed"], 36)

    def test_speed_985(self):
        self.s["L"] = 98.5
        self.assertAlmostEqual(measure(self.r, self.s)["speed"], 35.46)

    def test_offset_sign(self):
        self.s["sync"].update(offset_start=2, offset_end=2)
        self.assertEqual(measure(self.r, self.s)["dt"], 12)

    def test_linear_drift(self):
        self.s["sync"].update(offset_start=1, offset_end=3, anchor_start=0, anchor_end=20)
        self.assertAlmostEqual(corrected(10, "B", self.s["sync"]), 12)

    def test_reverse_direction(self):
        self.r.update(direction="B→A", tA=11, tB=1)
        self.assertEqual(measure(self.r, self.s)["speed"], 36)

    def test_not_absolute(self):
        self.r.update(tA=11, tB=1)
        self.assertIsNone(measure(self.r, self.s)["speed"])

    def test_buffer(self):
        r = self.s["records"][-1]
        m = measure(r, self.s)
        self.assertTrue(m["valid"])
        self.assertEqual(m["interval"], 0)

    def test_missing_timestamp(self):
        self.r.pop("tB")
        self.assertIsNone(measure(self.r, self.s)["speed"])

    def test_missing_sync(self):
        self.s["sync"]["verified"] = False
        self.assertIsNone(measure(self.r, self.s)["speed"])

    def test_count_independent(self):
        r = summary(self.s)["rows"][0]
        self.assertEqual(r["N_observed"], 13)
        self.assertEqual(r["ns"], 6)
        self.assertEqual(r["q_equivalent"], 2340)
        self.assertIsNone(r["N15"])

    def test_fifteen_minute(self):
        self.s["end"] = 900
        self.assertEqual(summary(self.s)["rows"][0]["q_equivalent"], 52)

    def test_empty_and_single(self):
        p = self.s["protocol"]
        self.assertIsNone(stats([], p)["Mean"])
        self.assertIsNone(stats([36], p)["SD"])
        self.assertIsNone(stats([36], p)["V85"])

    def test_independent_stats(self):
        z = stats([10, 20, 30, 40], self.s["protocol"])
        self.assertEqual(z["Mean"], 25)
        self.assertAlmostEqual(z["SD"], math.sqrt(500 / 3))
        self.assertEqual(z["Median"], 25)
        self.assertAlmostEqual(z["V85"], 35.5)
        self.assertAlmostEqual(z["CI"][1], 45.5426025676, places=6)

    def test_bootstrap_seed(self):
        p = self.s["protocol"]
        self.assertEqual(stats([10, 20, 30], p), stats([10, 20, 30], p))

    def test_sampling_seed(self):
        self.assertEqual(plan(100, 0.2, 0.05, 43), plan(100, 0.2, 0.05, 43))

    def test_rare_census(self):
        self.assertEqual(plan(5, 0.2, 0.05, 43, rare=True)["selected"], [1, 2, 3, 4, 5])

    def test_fpc_guard(self):
        self.assertRaises(ValueError, plan, 100, 0.2, 0.05, 43, True, False)

    def test_disproportionate_no_pool(self):
        self.s["protocol"]["sampling"] = "stratified"
        self.assertIsNone(summary(self.s)["rows"][0]["stats"]["Mean"])

    def test_qc_stop_retained(self):
        self.r["qc"] = [4]
        self.assertTrue(measure(self.r, self.s)["valid"])

    def test_exclusion_retained_raw(self):
        self.s["records"][0]["decision"] = "exclude"
        d = summary(self.s)
        self.assertEqual(len(d["records"]), 6)
        self.assertEqual(d["rows"][0]["ns"], 5)

    def test_fps_and_vfr(self):
        a = metadata(self.s["videoA"])
        b = metadata(self.s["videoB"])
        self.assertNotEqual(a["fps"], b["fps"])
        v = index_video(DEMO_DIR / "synthetic_VFR.mp4")
        self.assertEqual(v["timing"], "VFR")
        self.assertNotEqual(
            v["frames"][2]["time"] - v["frames"][1]["time"],
            v["frames"][1]["time"] - v["frames"][0]["time"],
        )
        self.assertTrue(frame_bytes(v["id"], 2).startswith(b"\xff\xd8"))

    def test_exact_frame_decode(self):
        self.assertNotEqual(frame_bytes(self.s["videoA"], 10), frame_bytes(self.s["videoA"], 11))

    def test_agreement(self):
        a = agreement([(10, 11), (20, 19)])
        self.assertEqual(a["bias"], 0)
        self.assertEqual(a["MAE"], 1)
        self.assertEqual(a["RMSE"], 1)

    def test_persist_recover_api(self):
        ss = copy.deepcopy(self.s)
        ss["id"] = str(uuid.uuid4())
        ss = save(ss, "test temporary session")

        def call(op, v):
            nonlocal ss
            r = self.c.post(
                "/api/action/" + ss["id"], json={"op": op, "value": v, "revision": ss["revision"]}
            )
            self.assertEqual(r.status_code, 200, r.json)
            ss = r.json

        call("entry", dict(direction="A→B", type="MC", frame=20, description="Synthetic vehicle"))
        rid = ss["records"][-1]["id"]
        call("exit", dict(id=rid, frame=240))
        call(
            "record",
            dict(
                id=rid,
                decision="keep",
                matching="confirmed",
                reviewer="Test",
                reason="Known fixture",
                qc=[0],
            ),
        )
        self.assertEqual(measure(ss["records"][-1], ss)["speed"], 36)
        saved = get(ss["id"])
        self.assertEqual(saved, ss)
        sync = copy.deepcopy(ss["sync"])
        sync.update(offset_start=2, offset_end=2)
        call("settings", {"sync": sync})
        self.assertEqual(measure(ss["records"][-1], ss)["speed"], 30)
        old = self.c.get("/api/history/" + ss["id"]).json[-1]["seq"]
        restored = self.c.post(f"/api/restore/{ss['id']}/{old}").json
        self.assertEqual(len(restored["records"]), 6)
        with db() as c:
            c.execute("DELETE FROM sessions WHERE id=?", (ss["id"],))
            c.execute("DELETE FROM history WHERE session=?", (ss["id"],))

    def test_measurement_readiness_messages(self):
        ss = copy.deepcopy(self.s)
        ss["observer"] = ""
        ss["L"] = None
        ss["sync"]["verified"] = False
        ss["line_locked"]["A"] = False
        missing = measurement_readiness(ss)
        self.assertIn("nhập tên người thao tác", missing)
        self.assertIn("nhập khoảng cách L", missing)
        self.assertIn("xác nhận đồng bộ và căn cứ", missing)
        self.assertIn("vẽ và khóa hai vạch A, B", missing)

    def test_line_requires_two_valid_points(self):
        ss = copy.deepcopy(self.s)
        ss["id"] = str(uuid.uuid4())
        ss["line_locked"]["A"] = False
        ss = save(ss, "test line validation")
        r = self.c.post(
            "/api/action/" + ss["id"],
            json={
                "op": "line",
                "value": {"camera": "A", "points": None, "locked": True},
                "revision": ss["revision"],
            },
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("hai điểm", r.json["error"])
        with db() as c:
            c.execute("DELETE FROM sessions WHERE id=?", (ss["id"],))
            c.execute("DELETE FROM history WHERE session=?", (ss["id"],))

    def test_packaged_static_resources(self):
        for path in ["/", "/static/app.js", "/static/style.css"]:
            response = self.c.get(path)
            self.assertEqual(response.status_code, 200, path)
            response.close()

    def test_runtime_paths_are_isolated(self):
        for path in [DATA_DIR, OUTPUT_DIR, DEMO_DIR]:
            self.assertTrue(path.is_relative_to(_root))

    def test_database_connection_closed(self):
        import sqlite3

        with db() as connection:
            connection.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")

    def test_backup_endpoint(self):
        response = self.c.get("/api/backup")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"SQLite format 3"))
        response.close()

    def test_export_after_package_move(self):
        import zipfile

        from video_ab.exports import export_bundle

        path = export_bundle(self.s)
        self.assertTrue(path.is_relative_to(OUTPUT_DIR))
        with zipfile.ZipFile(path) as bundle:
            self.assertIsNone(bundle.testzip())
            self.assertTrue(any(name.endswith("Survey.xlsx") for name in bundle.namelist()))
