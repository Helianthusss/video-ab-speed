"""Scientific calculations. All times seconds in the A reference clock."""

import math
import random

import numpy as np
from scipy.stats import t

CLASSES = {
    "MC": "Xe máy",
    "Car": "Ô tô con",
    "Light truck/Van": "Xe tải nhẹ / van",
    "Bus": "Xe buýt",
    "Truck": "Xe tải",
    "Other": "Khác",
}
DEMO = "DỮ LIỆU MINH HỌA — KHÔNG DÙNG LÀM KẾT QUẢ NGHIÊN CỨU"


def corrected(raw, camera, sync):
    if raw is None or not sync.get("verified"):
        return None
    if camera == "A":
        return raw
    return (
        raw
        + sync["offset_start"]
        + (raw - sync["anchor_start"])
        * (sync["offset_end"] - sync["offset_start"])
        / (sync["anchor_end"] - sync["anchor_start"])
    )


def inverse_B(value, s):
    drift = (s["offset_end"] - s["offset_start"]) / (s["anchor_end"] - s["anchor_start"])
    return (value - s["offset_start"] + s["anchor_start"] * drift) / (1 + drift)


def measure(r, s):
    a = corrected(r.get("tA"), "A", s["sync"])
    b = corrected(r.get("tB"), "B", s["sync"])
    dt = None if a is None or b is None else (b - a if r["direction"] == "A→B" else a - b)
    L = s["L"]
    v = 3.6 * L / dt if dt is not None and dt > 0 and L and L > 0 else None
    entry = a if r["direction"] == "A→B" else b
    warnings = []
    if not s["sync"]["verified"]:
        warnings.append("Thiếu căn cứ đồng bộ")
    if dt is not None and dt <= 0:
        warnings.append("Thời gian hành trình không dương")
    if not L or L <= 0:
        warnings.append("L không dương")
    if a is None or b is None:
        warnings.append("Thiếu timestamp / chưa khớp")
    if entry is not None and not s["start"] <= entry < s["end"]:
        warnings.append("Mốc đầu ngoài phiên")
    if not r.get("type") or not r.get("observer"):
        warnings.append("Thiếu class / người thao tác")
    if v and not s["protocol"]["warning_speed"][0] <= v <= s["protocol"]["warning_speed"][1]:
        warnings.append("Tốc độ cần rà soát; không tự loại")
    interval = (
        int((entry - s["start"]) // s["interval_seconds"])
        if entry is not None and s["start"] <= entry < s["end"]
        else None
    )
    return dict(
        tA_corrected=a,
        tB_corrected=b,
        dt=dt,
        speed=v,
        interval=interval,
        warnings=warnings,
        valid=v is not None
        and interval is not None
        and r.get("decision") == "keep"
        and r.get("matching") == "confirmed",
        relative_uncertainty=math.hypot(s["uL"] / L, s["uT"] / dt)
        if v and s.get("uL") is not None and s.get("uT") is not None
        else None,
    )


def stats(values, p):
    x = np.asarray(values, dtype=float)
    n = len(x)
    result = dict(n=n, Mean=None, SD=None, CV=None, Median=None, V85=None, CI=None, P85_CI=None)
    if not n:
        return result
    mean = float(np.mean(x))
    result.update(Mean=mean, Median=float(np.quantile(x, 0.5, method="linear")))
    if n < 2:
        return result
    sd = float(np.std(x, ddof=1))
    result.update(SD=sd, CV=sd / mean if mean else None)
    if p.get("iid_ci"):
        d = float(t.ppf(0.975, n - 1) * sd / math.sqrt(n))
        result["CI"] = [mean - d, mean + d]
    if p.get("allow_percentile"):
        result["V85"] = float(np.quantile(x, 0.85, method="linear"))
        rng = np.random.default_rng(p["seed"])
        bs = [
            float(np.quantile(rng.choice(x, n), 0.85, method="linear"))
            for _ in range(p["bootstrap"])
        ]
        if p.get("iid_ci"):
            result["P85_CI"] = np.quantile(bs, [0.025, 0.975], method="linear").tolist()
    return result


def plan(N, cv, e, seed, fpc=False, eligible=False, rare=False):
    if not isinstance(N, int) or N < 1 or cv <= 0 or not 0 < e < 1:
        raise ValueError("N nguyên dương, CV > 0, 0 < precision < 1")
    if fpc and not eligible:
        raise ValueError("FPC cần xác nhận đúng quần thể lấy mẫu không hoàn lại")
    n0 = (1.96 * cv / e) ** 2
    n = math.ceil(n0 / (1 + (n0 - 1) / N)) if fpc else math.ceil(n0)
    n = min(N, max(1, n))
    k = 1 if rare else max(1, math.floor(N / n))
    r = random.Random(seed).randint(1, k)
    return dict(
        N=N,
        CV=cv,
        precision=e,
        n0=math.ceil(n0),
        n_target=n,
        k=k,
        rounding="floor N/n_target; rare k=1",
        start=r,
        seed=seed,
        fpc=fpc,
        eligible=eligible,
        selected=list(range(r, N + 1, k)),
        inclusion_probability=1 / k,
    )


def agreement(pairs):
    if not pairs:
        return dict(n=0, bias=None, MAE=None, RMSE=None, limits=None)
    d = np.array([b - a for a, b in pairs])
    n = len(d)
    bias = float(d.mean())
    sd = float(d.std(ddof=1)) if n > 1 else None
    return dict(
        n=n,
        bias=bias,
        MAE=float(np.abs(d).mean()),
        RMSE=float(np.sqrt((d * d).mean())),
        limits=[bias - 1.96 * sd, bias + 1.96 * sd] if sd is not None else None,
        bland_altman=[{"mean": (a + b) / 2, "difference": b - a} for a, b in pairs],
    )


def summary(s):
    records = [dict(r, **measure(r, s)) for r in s["records"]]
    rows = []
    count_intervals = math.ceil((s["end"] - s["start"]) / s["interval_seconds"])
    for direction in ["A→B", "B→A"]:
        for interval in range(count_intervals):
            duration = min(
                s["interval_seconds"], s["end"] - s["start"] - interval * s["interval_seconds"]
            )
            rr = [r for r in records if r["direction"] == direction and r["interval"] == interval]
            flow = [
                f
                for f in s["flow"]
                if f["direction"] == direction
                and f["interval"] == interval
                and f["section"] == s["reference"]
            ]
            N = sum(f["count"] for f in flow) if flow else None
            by = {
                c: stats([r["speed"] for r in rr if r["valid"] and r["type"] == c], s["protocol"])
                for c in CLASSES
            }
            valid = [r for r in rr if r["valid"]]
            # No naive full-stream inference under disproportionate / incomplete sampling.
            total = (
                stats([r["speed"] for r in valid], s["protocol"])
                if s["protocol"]["sampling"] == "census"
                else stats([], s["protocol"])
            )
            mc = by["MC"]["Mean"]
            car = by["Car"]["Mean"]
            diff = mc - car if mc is not None and car is not None else None
            rows.append(
                dict(
                    Site=s["site"],
                    direction=direction,
                    interval=interval,
                    duration=duration,
                    N15=N if duration == 900 else None,
                    N_observed=N,
                    q_equivalent=N * 3600 / duration if N is not None else None,
                    MC_percent=100 * sum(f["count"] for f in flow if f["type"] == "MC") / N
                    if N
                    else None,
                    ns=len(valid),
                    selected=sum(r.get("sampling_status") == "selected" for r in rr),
                    matched=sum(r.get("matching") == "confirmed" for r in rr),
                    stats=total,
                    classes=by,
                    Diff=diff,
                    Diff_abs=abs(diff) if diff is not None else None,
                    source_ids=[r["id"] for r in valid],
                    scope="Mẫu xe giữ lại; không khẳng định đại diện toàn dòng"
                    if s["protocol"]["sampling"] == "census"
                    else "Không gộp toàn dòng khi chưa có trọng số được xác nhận",
                )
            )
    return {"records": records, "rows": rows}
