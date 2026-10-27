import json
import os
import sys
import time
from pathlib import Path

from .yolo_jobs import write

VEHICLES = ("car", "motorcycle", "truck", "bus", "bicycle")


def side(line, point):
    """Which side of the line the point lies on, in normalised image space."""
    (x1, y1), (x2, y2) = line
    x, y = point
    value = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    if value > 1e-9:
        return 1
    if value < -1e-9:
        return -1
    return 0


def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segs_intersect(p1, p2, p3, p4):
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


def line_intersects_box(line, b):
    (lx1, ly1), (lx2, ly2) = line
    bx1, by1, bx2, by2 = b
    if (bx1 <= lx1 <= bx2 and by1 <= ly1 <= by2) or (bx1 <= lx2 <= bx2 and by1 <= ly2 <= by2):
        return True
    corners = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2)]
    for i in range(4):
        if segs_intersect((lx1, ly1), (lx2, ly2), corners[i], corners[(i + 1) % 4]):
            return True
    return False


def bottom_center_crossed(line, previous, current):
    """Detect a crossing of the finite line by consecutive ground-contact points."""
    if previous is None:
        return False
    (x1, y1), (x2, y2) = line

    def signed(point):
        return (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)

    before, after = signed(previous), signed(current)
    if abs(before) < 1e-9 and abs(after) < 1e-9 or before * after > 0:
        return False
    fraction = before / (before - after)
    if not 0 <= fraction <= 1:
        return False
    x = previous[0] + fraction * (current[0] - previous[0])
    y = previous[1] + fraction * (current[1] - previous[1])
    return (
        min(x1, x2) - 1e-6 <= x <= max(x1, x2) + 1e-6
        and min(y1, y2) - 1e-6 <= y <= max(y1, y2) + 1e-6
    )


def crossings(tracks, lines, distance):
    """Travel time and speed for tracks that crossed both lines."""
    rows = []
    for ident, track in sorted(tracks.items()):
        times = {}
        for name in ("A", "B"):
            line = lines.get(name)
            if not line or len(line) != 2:
                continue
            previous = None
            for item in track["path"]:
                point, moment = item[0], item[1]
                box = item[2] if len(item) > 2 else None
                current = ((box[0] + box[2]) / 2, box[3]) if box else point
                if bottom_center_crossed(line, previous, current):
                    times[name] = moment
                    break
                previous = current
        row = dict(
            track_id=ident,
            label=track["label"],
            first_time=track["path"][0][1],
            last_time=track["path"][-1][1],
            frames=len(track["path"]),
            time_A=times.get("A"),
            time_B=times.get("B"),
        )
        if times.get("A") is not None and times.get("B") is not None:
            delta = abs(times["B"] - times["A"])
            row["travel_seconds"] = round(delta, 4)
            row["direction"] = "A→B" if times["B"] > times["A"] else "B→A"
            if delta > 0 and distance and distance > 0:
                row["speed_kmh"] = round(3.6 * distance / delta, 2)
        rows.append(row)
    return rows


def crop_box_for_line(line, width, height, margin=0.35):
    if not line or len(line) != 2:
        return None
    xs = [max(0.0, min(1.0, p[0])) for p in line]
    ys = [max(0.0, min(1.0, p[1])) for p in line]
    x1 = int(max(0, (min(xs) - margin) * width))
    x2 = int(min(width, (max(xs) + margin) * width))
    y1 = int(max(0, (min(ys) - margin) * height))
    y2 = int(min(height, (max(ys) + margin) * height))
    if x2 - x1 < width * 0.25 or y2 - y1 < height * 0.20:
        return None
    return x1, y1, x2, y2


def map_box_from_crop(xyxyn, crop, width, height):
    if not crop:
        return xyxyn
    x1, y1, x2, y2 = crop
    cw, ch = x2 - x1, y2 - y1
    left, top, right, bottom = xyxyn
    return [
        (x1 + left * cw) / width,
        (y1 + top * ch) / height,
        (x1 + right * cw) / width,
        (y1 + bottom * ch) / height,
    ]


def run(dest):
    state = json.loads((dest / "status.json").read_text(encoding="utf-8"))
    try:
        os.environ["YOLO_CONFIG_DIR"] = str(dest / "config")
        (dest / "config").mkdir(exist_ok=True)
        import av
        import torch
        from ultralytics import YOLO

        config = json.loads((dest / "input.json").read_text(encoding="utf-8"))
        import warnings
        warnings.filterwarnings("ignore", message=".*half.*")
        torch.set_num_threads(max(4, os.cpu_count() or 4))
        device = config["device"]
        if device == "auto":
            device = "0" if torch.cuda.is_available() else "cpu"
        is_cuda = (device != "cpu")
        if is_cuda:
            torch.backends.cudnn.benchmark = True
        state.update(status="loading_model", device=device)
        write(dest / "status.json", state)
        model = YOLO(config["weights"])
        ids = [i for i, name in model.names.items() if name in VEHICLES]
        if not ids:
            raise ValueError("Weights không có nhãn phương tiện COCO được hỗ trợ")
        state.update(status="running")
        write(dest / "status.json", state)
        m = config["media"]
        selected_indices = set(config["selected_indices"])
        selected = [f for f in m["frames"] if f["index"] in selected_indices]
        stride = int(config.get("stride", state.get("stride", 1)) or 1)
        by_pts = {f["pts"]: f for f in selected}
        rows = []
        tracks = {}
        lines = config.get("lines") or {}
        use_roi = bool(config.get("roi", True))
        begun = time.monotonic()
        with torch.inference_mode():
            with av.open(m["path"]) as source:
                st = source.streams.video[0]
                st.thread_type = "AUTO"
                if hasattr(st, "codec_context") and st.codec_context:
                    st.codec_context.thread_count = min(8, os.cpu_count() or 4)
                source.seek(selected[0]["pts"], stream=st, backward=True)
                for frame in source.decode(st):
                    if frame.pts > selected[-1]["pts"]:
                        break
                    if frame.pts not in by_pts:
                        continue
                    f = by_pts[frame.pts]
                    # Tracking keeps one identity across frames, which is what makes a
                    # crossing time, and therefore a travel time, possible at all.
                    image = frame.to_ndarray(format="bgr24")
                    height, width = image.shape[:2]
                    crop = crop_box_for_line(lines.get(state["camera"]), width, height) if use_roi else None
                    inference_image = image[crop[1]:crop[3], crop[0]:crop[2]] if crop else image
                    result = model.track(
                        inference_image,
                        persist=True,
                        tracker="bytetrack.yaml",
                        classes=ids,
                        conf=state["confidence"],
                        imgsz=640,
                        device=device,
                        half=is_cuda,
                        verbose=False,
                    )[0]
                    boxes = []
                    for b in result.boxes:
                        label = model.names[int(b.cls.item())]
                        xyxyn = map_box_from_crop(b.xyxyn[0].tolist(), crop, width, height)
                        ident = int(b.id.item()) if b.id is not None else None
                        boxes.append(
                            dict(
                                label=label,
                                confidence=round(float(b.conf.item()), 4),
                                xyxyn=xyxyn,
                                track_id=ident,
                            )
                        )
                        if ident is not None:
                            point = ((xyxyn[0] + xyxyn[2]) / 2, xyxyn[3])
                            track = tracks.setdefault(ident, dict(label=label, path=[]))
                            track["path"].append((point, f["time"], xyxyn))
                    rows.append(
                        dict(
                            frame=f["index"],
                            pts=f["pts"],
                            time_base=f["time_base"],
                            time=f["time"],
                            boxes=boxes,
                            roi=bool(crop),
                        )
                    )
                    state["processed"] += 1
                    if state["processed"] % 10 == 0:
                        write(dest / "status.json", state)
        if len(rows) != state["total"]:
            raise ValueError("Không giải mã đủ frame")
        table = crossings(tracks, lines, config.get("distance"))
        measured = [r for r in table if r.get("speed_kmh") is not None]
        write(
            dest / "detections.json",
            dict(
                session_id=state["session_id"],
                camera=state["camera"],
                media_id=state["media_id"],
                weights=Path(config["weights"]).name,
                crossing_method="bottom-center-v2",
                distance_m=config.get("distance"),
                lines=lines,
                stride=stride,
                roi=use_roi,
                frames=rows,
                tracks=table,
                note=(
                    "Tracking estimate. The reference point is the bottom centre of the "
                    "box, not the vehicle front, so speeds are for review only and are "
                    "not survey measurements. Track identities are not unique vehicle "
                    "counts."
                ),
            ),
        )
        state.update(
            status="done",
            elapsed_seconds=round(time.monotonic() - begun, 2),
            detections=sum(len(r["boxes"]) for r in rows),
            tracks=len(table),
            crossed_both=len(measured),
        )
    except Exception as exc:
        state.update(status="failed", error=str(exc))
    write(dest / "status.json", state)


if __name__ == "__main__":
    run(Path(sys.argv[1]))

