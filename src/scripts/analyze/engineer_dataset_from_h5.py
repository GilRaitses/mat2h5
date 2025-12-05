"""
Enhanced engineer_dataset_from_h5.py for simulation export
----------------------------------------------------------

Adds stimulus-window and cycle-level aggregates, per-track per-window metrics,
population aggregates, and concurrency estimation. Uses LED-derived ton/toff
windows, sloc positions, and lengthPerPixel from root.
"""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import h5py
import numpy as np


# -----------------------
# Data classes
# -----------------------

@dataclass
class Reversal:
    start_idx: int
    end_idx: int
    start_time: float
    end_time: float
    duration: float
    mean_speed: float = 0.0

    def to_dict(self) -> dict:
        return {
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "mean_speed": self.mean_speed,
        }


@dataclass
class TurnEvent:
    idx: int
    time: float
    angle_change: float
    direction: str

    def to_dict(self) -> dict:
        return {
            "idx": self.idx,
            "time": self.time,
            "angle_change": self.angle_change,
            "direction": self.direction,
        }


@dataclass
class TrackWindowStats:
    track_num: int
    window_id: int
    window_start: float
    window_end: float
    reversals: int
    reversal_duration: float
    turns: int
    turn_rate_per_min: float
    frac_negative_speedrunvel: float
    mean_speedrunvel: float
    total_duration: float

    def to_dict(self) -> dict:
        return {
            "track_num": self.track_num,
            "window_id": self.window_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "reversals": self.reversals,
            "reversal_duration": self.reversal_duration,
            "turns": self.turns,
            "turn_rate_per_min": self.turn_rate_per_min,
            "frac_negative_speedrunvel": self.frac_negative_speedrunvel,
            "mean_speedrunvel": self.mean_speedrunvel,
            "total_duration": self.total_duration,
        }


@dataclass
class TrackAnalysis:
    track_num: int
    total_duration: float
    reversals: List[Reversal] = field(default_factory=list)
    turn_events: List[TurnEvent] = field(default_factory=list)
    mean_speed: float = 0.0
    mean_speedrunvel: float = 0.0
    fraction_reversing: float = 0.0

    @property
    def num_reversals(self) -> int:
        return len(self.reversals)

    @property
    def total_reversal_duration(self) -> float:
        return sum(r.duration for r in self.reversals)

    @property
    def turn_rate(self) -> float:
        if self.total_duration > 0:
            return len(self.turn_events) / (self.total_duration / 60.0)
        return 0.0

    def to_dict(self) -> dict:
        return {
            "track_num": self.track_num,
            "total_duration": self.total_duration,
            "num_reversals": self.num_reversals,
            "total_reversal_duration": self.total_reversal_duration,
            "reversals": [r.to_dict() for r in self.reversals],
            "num_turns": len(self.turn_events),
            "turn_rate": self.turn_rate,
            "turn_events": [t.to_dict() for t in self.turn_events],
            "mean_speed": self.mean_speed,
            "mean_speedrunvel": self.mean_speedrunvel,
            "fraction_reversing": self.fraction_reversing,
        }


# -----------------------
# Core computations
# -----------------------

def compute_heading_unit_vector(shead: np.ndarray, smid: np.ndarray) -> np.ndarray:
    if shead.shape[0] != 2:
        shead = shead.T
    if smid.shape[0] != 2:
        smid = smid.T
    head_vec = shead - smid
    norms = np.sqrt(head_vec[0, :] ** 2 + head_vec[1, :] ** 2)
    norms[norms == 0] = 1.0
    return head_vec / norms


def compute_velocity_and_speed(xpos: np.ndarray, ypos: np.ndarray, times: np.ndarray):
    dx = np.diff(xpos)
    dy = np.diff(ypos)
    dt = np.diff(times)
    distance = np.sqrt(dx**2 + dy**2)
    speed = np.zeros_like(distance)
    valid = dt > 0
    speed[valid] = distance[valid] / dt[valid]
    velocity_vec = np.zeros((2, len(dx)))
    valid_dist = distance > 0
    velocity_vec[0, valid_dist] = dx[valid_dist] / distance[valid_dist]
    velocity_vec[1, valid_dist] = dy[valid_dist] / distance[valid_dist]
    return velocity_vec, speed


def compute_speedrunvel(
    shead: np.ndarray,
    smid: np.ndarray,
    xpos: np.ndarray,
    ypos: np.ndarray,
    times: np.ndarray,
    length_per_pixel: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    xpos_cm = xpos * length_per_pixel
    ypos_cm = ypos * length_per_pixel
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    velocity_vec, speed = compute_velocity_and_speed(xpos_cm, ypos_cm, times)
    cos_theta = np.sum(velocity_vec * head_unit_vec[:, :-1], axis=0)
    speedrunvel = speed * cos_theta
    times_out = times[:-1]
    return speedrunvel, times_out, head_unit_vec


def detect_reversals(times: np.ndarray, speedrunvel: np.ndarray, min_duration: float = 3.0):
    if len(times) == 0 or len(speedrunvel) == 0:
        return []
    reversals = []
    in_rev = False
    start_idx = None
    start_time = None
    for i, val in enumerate(speedrunvel):
        neg = val < 0
        if neg and not in_rev:
            in_rev = True
            start_idx = i
            start_time = times[i]
        elif not neg and in_rev:
            in_rev = False
            if start_idx is not None:
                dur = times[i] - start_time
                if dur >= min_duration:
                    mean_speed = float(np.abs(np.mean(speedrunvel[start_idx:i])))
                    reversals.append(
                        Reversal(
                            start_idx=start_idx,
                            end_idx=i - 1,
                            start_time=start_time,
                            end_time=times[i - 1],
                            duration=dur,
                            mean_speed=mean_speed,
                        )
                    )
            start_idx = None
    if in_rev and start_idx is not None:
        dur = times[-1] - start_time
        if dur >= min_duration:
            mean_speed = float(np.abs(np.mean(speedrunvel[start_idx:])))
            reversals.append(
                Reversal(
                    start_idx=start_idx,
                    end_idx=len(speedrunvel) - 1,
                    start_time=start_time,
                    end_time=times[-1],
                    duration=dur,
                    mean_speed=mean_speed,
                )
            )
    return reversals


def detect_turn_events(times: np.ndarray, head_unit_vec: np.ndarray, angle_threshold: float = 45.0, min_frames: int = 3):
    if head_unit_vec.shape[1] < min_frames:
        return []
    angles = np.arctan2(head_unit_vec[1, :], head_unit_vec[0, :])
    angle_diff = np.diff(np.unwrap(angles))
    angle_diff_deg = np.rad2deg(angle_diff)
    turn_events = []
    i = 0
    while i < len(angle_diff) - min_frames:
        cumsum = 0.0
        for j in range(i, min(i + 30, len(angle_diff))):
            cumsum += angle_diff_deg[j]
            if abs(cumsum) >= angle_threshold:
                direction = "left" if cumsum > 0 else "right"
                turn_events.append(
                    TurnEvent(idx=i, time=times[i], angle_change=abs(cumsum), direction=direction)
                )
                i = j + min_frames
                break
        else:
            i += 1
    return turn_events


# -----------------------
# Stimulus windowing
# -----------------------

def compute_ton_toff(led_values: np.ndarray, threshold: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    if threshold is None:
        threshold = float(np.max(led_values)) * 0.1 if len(led_values) > 0 else 0.0
    is_on = led_values > threshold
    ton = is_on
    toff = ~is_on
    return ton, toff


def derive_windows_from_led(eti: np.ndarray, led1: np.ndarray) -> List[Tuple[float, float, int]]:
    """
    Derive stimulus windows from LED1 ton/toff transitions.
    Returns list of (start_time, end_time, window_id) in order.
    """
    ton, toff = compute_ton_toff(led1)
    windows = []
    in_on = False
    start = None
    win_id = 0
    for i, t in enumerate(eti):
        if ton[i] and not in_on:
            in_on = True
            start = t
            win_id += 1
        if not ton[i] and in_on:
            end = eti[i]
            windows.append((start, end, win_id))
            in_on = False
            start = None
    if in_on and start is not None:
        windows.append((start, float(eti[-1]), win_id))
    return windows


def slice_by_window(times: np.ndarray, values: np.ndarray, win_start: float, win_end: float):
    mask = (times >= win_start) & (times <= win_end)
    return values[mask], times[mask]


# -----------------------
# Loading tracks
# -----------------------

def load_track_from_h5(f: h5py.File, track_key: str) -> Optional[Dict]:
    try:
        tg = f[f"tracks/{track_key}"]
        dq = tg["derived_quantities"]
        shead = dq["shead"][:]
        smid = dq["smid"][:]
        loc = dq["sloc"][:] if "sloc" in dq else tg["points"]["loc"][:]
        if "eti" in dq:
            eti = dq["eti"][:]
        else:
            eti = f["eti"][:]
        lpp = 0.01
        if "lengthPerPixel" in f:
            lpp = float(f["lengthPerPixel"][()])
        elif "metadata" in f and "lengthPerPixel" in f["metadata"].attrs:
            lpp = float(f["metadata"].attrs["lengthPerPixel"])
        return {"shead": shead, "smid": smid, "loc": loc, "eti": eti, "length_per_pixel": lpp}
    except Exception as e:
        print(f"Error loading track {track_key}: {e}")
        return None


# -----------------------
# Analysis per track
# -----------------------

def analyze_track(track_data: Dict, track_num: int, min_reversal_duration: float, angle_threshold: float):
    shead = track_data["shead"]
    smid = track_data["smid"]
    loc = track_data["loc"]
    eti = track_data["eti"]
    lpp = track_data["length_per_pixel"]

    if loc.shape[0] == 2:
        xpos = loc[0, :]
        ypos = loc[1, :]
    else:
        xpos = loc[:, 0]
        ypos = loc[:, 1]

    speedrunvel, times_sr, head_unit_vec = compute_speedrunvel(shead, smid, xpos, ypos, eti, lpp)
    reversals = detect_reversals(times_sr, speedrunvel, min_duration=min_reversal_duration)
    turn_events = detect_turn_events(times_sr, head_unit_vec, angle_threshold=angle_threshold)

    total_duration = eti[-1] - eti[0] if len(eti) > 1 else 0.0
    mean_speed = float(np.mean(np.abs(speedrunvel))) if len(speedrunvel) > 0 else 0.0
    mean_speedrunvel = float(np.mean(speedrunvel)) if len(speedrunvel) > 0 else 0.0
    fraction_reversing = float(np.sum(speedrunvel < 0) / len(speedrunvel)) if len(speedrunvel) > 0 else 0.0

    return (
        TrackAnalysis(
            track_num=track_num,
            total_duration=total_duration,
            reversals=reversals,
            turn_events=turn_events,
            mean_speed=mean_speed,
            mean_speedrunvel=mean_speedrunvel,
            fraction_reversing=fraction_reversing,
        ),
        times_sr,
        speedrunvel,
    )


# -----------------------
# Windowed metrics
# -----------------------

def compute_track_window_stats(track: TrackAnalysis, times_sr: np.ndarray, speedrunvel: np.ndarray, windows):
    stats = []
    for (ws, we, wid) in windows:
        # Slice speedrunvel within window
        mask = (times_sr >= ws) & (times_sr <= we)
        sr_slice = speedrunvel[mask]
        dur = we - ws
        revs = [r for r in track.reversals if r.start_time <= we and r.end_time >= ws]
        rev_count = len(revs)
        rev_dur = sum(r.duration for r in revs)
        turns = [t for t in track.turn_events if ws <= t.time <= we]
        turn_count = len(turns)
        turn_rate = (turn_count / (dur / 60.0)) if dur > 0 else 0.0
        frac_neg = float(np.sum(sr_slice < 0) / len(sr_slice)) if len(sr_slice) > 0 else 0.0
        mean_sr = float(np.mean(sr_slice)) if len(sr_slice) > 0 else 0.0
        stats.append(
            TrackWindowStats(
                track_num=track.track_num,
                window_id=wid,
                window_start=ws,
                window_end=we,
                reversals=rev_count,
                reversal_duration=rev_dur,
                turns=turn_count,
                turn_rate_per_min=turn_rate,
                frac_negative_speedrunvel=frac_neg,
                mean_speedrunvel=mean_sr,
                total_duration=dur,
            )
        )
    return stats


def aggregate_population_windows(track_window_stats: List[TrackWindowStats]) -> Dict:
    if not track_window_stats:
        return {}
    # group by window_id
    by_win = {}
    for tw in track_window_stats:
        by_win.setdefault(tw.window_id, []).append(tw)

    def stats(arr):
        if not arr:
            return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
        vals = np.array(arr, dtype=float)
        return {
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "std": float(np.std(vals)),
        }

    pop = {}
    for wid, lst in by_win.items():
        rev_counts = [x.reversals for x in lst]
        rev_durs = [x.reversal_duration for x in lst]
        turn_counts = [x.turns for x in lst]
        turn_rates = [x.turn_rate_per_min for x in lst]
        frac_neg = [x.frac_negative_speedrunvel for x in lst]
        mean_sr = [x.mean_speedrunvel for x in lst]
        pop[wid] = {
            "tracks": len(lst),
            "reversals": stats(rev_counts),
            "reversal_durations": stats(rev_durs),
            "turns": stats(turn_counts),
            "turn_rates_per_min": stats(turn_rates),
            "frac_negative_speedrunvel": stats(frac_neg),
            "mean_speedrunvel": stats(mean_sr),
        }
    return pop


def estimate_concurrency(track_analyses: List[TrackAnalysis], track_times: Dict[int, Tuple[float, float]], bin_size: float = 10.0):
    """
    Estimate active-track concurrency over time bins.
    track_times: dict track_num -> (t_start, t_end)
    """
    if not track_times:
        return []
    t_min = min(v[0] for v in track_times.values())
    t_max = max(v[1] for v in track_times.values())
    bins = np.arange(t_min, t_max + bin_size, bin_size)
    concurrency = []
    for i in range(len(bins) - 1):
        b0, b1 = bins[i], bins[i + 1]
        active = 0
        for _, (ts, te) in track_times.items():
            if te >= b0 and ts <= b1:
                active += 1
        concurrency.append({"bin_start": float(b0), "bin_end": float(b1), "active_tracks": active})
    return concurrency


# -----------------------
# Main analysis
# -----------------------

def analyze_h5_file(h5_path: Path, min_reversal_duration: float, angle_threshold: float) -> Dict:
    results = {
        "file": str(h5_path),
        "timestamp": datetime.now().isoformat(),
        "tracks": [],
        "summary": {},
        "windows": [],
        "track_windows": [],
        "population_windows": {},
        "concurrency": [],
    }

    with h5py.File(str(h5_path), "r") as f:
        if "tracks" not in f:
            return results
        # LED values for windows
        if "global_quantities" in f and "led1Val" in f["global_quantities"]:
            gq1 = f["global_quantities/led1Val"]
            led1 = gq1["yData"][:] if isinstance(gq1, h5py.Group) and "yData" in gq1 else gq1[:]
        else:
            led1 = np.array([])
        eti_root = f["eti"][:] if "eti" in f else None
        windows = []
        if eti_root is not None and len(led1) == len(eti_root) and len(led1) > 0:
            windows = derive_windows_from_led(eti_root, led1)
            results["windows"] = [{"id": wid, "start": float(ws), "end": float(we)} for (ws, we, wid) in windows]

        track_keys = list(f["tracks"].keys())
        track_analyses = []
        track_times = {}
        track_windows_stats = []

        for i, tk in enumerate(track_keys):
            td = load_track_from_h5(f, tk)
            if td is None:
                continue
            try:
                tnum = int(tk.replace("track_", "").replace("track", ""))
            except:
                tnum = i + 1

            ta, times_sr, speedrunvel = analyze_track(td, tnum, min_reversal_duration, angle_threshold)
            track_analyses.append(ta)
            track_times[tnum] = (float(td["eti"][0]), float(td["eti"][-1]))
            # per-window stats
            if windows:
                tws = compute_track_window_stats(ta, times_sr, speedrunvel, windows)
                track_windows_stats.extend(tws)

        results["tracks"] = [ta.to_dict() for ta in track_analyses]
        if track_windows_stats:
            results["track_windows"] = [t.to_dict() for t in track_windows_stats]
            results["population_windows"] = aggregate_population_windows(track_windows_stats)
        if track_times:
            results["concurrency"] = estimate_concurrency(track_analyses, track_times, bin_size=10.0)
        if track_analyses:
            results["summary"] = compute_summary_statistics(track_analyses)

    return results


def compute_summary_statistics(track_analyses: List[TrackAnalysis]) -> Dict:
    total_tracks = len(track_analyses)
    tracks_with_reversals = sum(1 for ta in track_analyses if ta.num_reversals > 0)
    all_reversals = [r for ta in track_analyses for r in ta.reversals]
    all_durations = [r.duration for r in all_reversals]
    all_turn_rates = [ta.turn_rate for ta in track_analyses]
    all_frac_rev = [ta.fraction_reversing for ta in track_analyses]

    def stats(arr):
        if not arr:
            return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
        vals = np.array(arr, dtype=float)
        return {
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "std": float(np.std(vals)),
        }

    return {
        "total_tracks": total_tracks,
        "tracks_with_reversals": tracks_with_reversals,
        "percent_tracks_with_reversals": 100.0 * tracks_with_reversals / total_tracks if total_tracks > 0 else 0.0,
        "total_reversal_events": len(all_reversals),
        "reversal_duration_stats": stats(all_durations),
        "turn_rate_stats": stats(all_turn_rates),
        "fraction_reversing_stats": stats(all_frac_rev),
    }


def process_directory(input_dir: Path, output_dir: Optional[Path], min_reversal_duration: float, angle_threshold: float) -> Dict:
    input_dir = Path(input_dir)
    h5_files = list(input_dir.glob("*.h5"))
    results_all = {"processed_at": datetime.now().isoformat(), "input_directory": str(input_dir), "files": []}
    for h5_path in h5_files:
        print(f"\nProcessing: {h5_path.name}")
        res = analyze_h5_file(h5_path, min_reversal_duration, angle_threshold)
        results_all["files"].append(res)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / f"{h5_path.stem}_analysis.json", "w") as f:
                json.dump(res, f, indent=2)
    if output_dir:
        with open(Path(output_dir) / "combined_analysis.json", "w") as f:
            json.dump(results_all, f, indent=2)
    return results_all


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced engineer dataset from H5 with stimulus-window aggregates")
    parser.add_argument("input", type=str, help="Input H5 file or directory (validated H5s)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output directory for JSON results")
    parser.add_argument("--min-duration", type=float, default=3.0, help="Minimum reversal duration (s)")
    parser.add_argument("--angle-threshold", type=float, default=45.0, help="Turn detection angle threshold (deg)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else None

    if input_path.is_file() and input_path.suffix == ".h5":
        res = analyze_h5_file(input_path, args.min_duration, args.angle_threshold)
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / f"{input_path.stem}_analysis.json", "w") as f:
                json.dump(res, f, indent=2)
        print(json.dumps(res["summary"], indent=2))
    elif input_path.is_dir():
        res = process_directory(input_path, output_dir, args.min_duration, args.angle_threshold)
        print(f"Processed {len(res['files'])} files.")
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

