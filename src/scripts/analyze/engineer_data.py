"""
Engineer Data Script for Reverse Crawl Detection
=================================================
Converts Mason's MATLAB reverse crawl detection methods to Python.
Processes H5 experiment files to extract:
  - Reverse crawl events (SpeedRunVel < 0 for > 3 seconds)
  - Turn rates (heading angle changes > 45 degrees)
  - Aggregate statistics (population averages, counts, durations)

ORIGINAL MASON SCRIPTS:
-----------------------
  - Just_ReverseCrawl_Matlab.m (SpeedRunVel computation)
  - Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m (behavior classification)
  - Misc2B.m (run statistics and reorientation events)
  Location: scripts/2025-11-20/mason's scritps/

Mathematical Method (from Mason Klein's scripts):
-------------------------------------------------
1. HeadVec = shead - smid (heading direction)
2. HeadUnitVec = HeadVec / ||HeadVec|| (normalized)
3. VelocityVec = displacement / ||displacement|| (normalized)
4. SpeedRun = ||displacement|| / dt (speed in cm/s)
5. CosThetaFactor = VelocityVec · HeadUnitVec (dot product)
6. SpeedRunVel = SpeedRun × CosThetaFactor (signed velocity)

Reversal Detection:
  - SpeedRunVel > 0 → Forward crawling
  - SpeedRunVel < 0 → Reverse crawling
  - Reversal event: SpeedRunVel < 0 for duration >= 3 seconds

Reference: scripts/2025-11-24/mason_scripts_documentation.qmd
"""

import numpy as np
import h5py
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime


@dataclass
class Reversal:
    """Represents a single reverse crawl event."""
    start_idx: int
    end_idx: int
    start_time: float
    end_time: float
    duration: float
    mean_speed: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'mean_speed': self.mean_speed
        }


@dataclass
class TurnEvent:
    """Represents a turn/reorientation event."""
    idx: int
    time: float
    angle_change: float  # in degrees
    direction: str  # 'left' or 'right'
    
    def to_dict(self) -> dict:
        return {
            'idx': self.idx,
            'time': self.time,
            'angle_change': self.angle_change,
            'direction': self.direction
        }


@dataclass
class TrackAnalysis:
    """Analysis results for a single track."""
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
        """Turns per minute."""
        if self.total_duration > 0:
            return len(self.turn_events) / (self.total_duration / 60.0)
        return 0.0
    
    def to_dict(self) -> dict:
        return {
            'track_num': self.track_num,
            'total_duration': self.total_duration,
            'num_reversals': self.num_reversals,
            'total_reversal_duration': self.total_reversal_duration,
            'reversals': [r.to_dict() for r in self.reversals],
            'num_turns': len(self.turn_events),
            'turn_rate': self.turn_rate,
            'turn_events': [t.to_dict() for t in self.turn_events],
            'mean_speed': self.mean_speed,
            'mean_speedrunvel': self.mean_speedrunvel,
            'fraction_reversing': self.fraction_reversing
        }


def compute_heading_unit_vector(shead: np.ndarray, smid: np.ndarray) -> np.ndarray:
    """
    Compute normalized heading unit vector from head and midpoint positions.
    
    HeadVec = shead - smid
    HeadUnitVec = HeadVec / ||HeadVec||
    
    Args:
        shead: Head positions, shape (2, N) or (N, 2)
        smid: Midpoint positions, shape (2, N) or (N, 2)
    
    Returns:
        HeadUnitVec: Normalized heading vectors, shape (2, N)
    """
    # Ensure shape is (2, N)
    if shead.shape[0] != 2:
        shead = shead.T
    if smid.shape[0] != 2:
        smid = smid.T
    
    # HeadVec = shead - smid
    head_vec = shead - smid
    
    # Compute norm for each time point
    norms = np.sqrt(head_vec[0, :]**2 + head_vec[1, :]**2)
    
    # Avoid division by zero
    norms[norms == 0] = 1.0
    
    # Normalize
    head_unit_vec = head_vec / norms
    
    return head_unit_vec


def compute_velocity_and_speed(
    xpos: np.ndarray, 
    ypos: np.ndarray, 
    times: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute velocity unit vectors and speed from position time series.
    
    VelocityVec = [dx, dy] / ||[dx, dy]||
    SpeedRun = ||[dx, dy]|| / dt
    
    Args:
        xpos: X positions (N,)
        ypos: Y positions (N,)
        times: Time values (N,)
    
    Returns:
        velocity_vec: Normalized velocity vectors, shape (2, N-1)
        speed: Speed values, shape (N-1,)
    """
    # Compute displacements
    dx = np.diff(xpos)
    dy = np.diff(ypos)
    dt = np.diff(times)
    
    # Compute distance
    distance = np.sqrt(dx**2 + dy**2)
    
    # Compute speed (distance / time)
    speed = np.zeros_like(distance)
    valid = dt > 0
    speed[valid] = distance[valid] / dt[valid]
    
    # Normalize velocity vectors
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
    length_per_pixel: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute SpeedRunVel (signed velocity indicating forward/reverse motion).
    
    SpeedRunVel = SpeedRun × CosThetaFactor
    
    where:
        CosThetaFactor = VelocityVec · HeadUnitVec
    
    Args:
        shead: Head positions, shape (2, N) or (N, 2)
        smid: Midpoint positions, shape (2, N) or (N, 2)
        xpos: X positions in pixels (N,)
        ypos: Y positions in pixels (N,)
        times: Time values (N,)
        length_per_pixel: Conversion factor (cm/pixel)
    
    Returns:
        speedrunvel: Signed velocity array (N-1,)
        times_out: Time values for speedrunvel (N-1,)
    """
    # Convert positions to cm
    xpos_cm = xpos * length_per_pixel
    ypos_cm = ypos * length_per_pixel
    
    # Compute heading unit vectors
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    
    # Compute velocity vectors and speed
    velocity_vec, speed = compute_velocity_and_speed(xpos_cm, ypos_cm, times)
    
    # Compute dot product (CosThetaFactor)
    # Use head_unit_vec at each frame (truncate to match velocity length)
    cos_theta = np.sum(velocity_vec * head_unit_vec[:, :-1], axis=0)
    
    # SpeedRunVel = speed × cos(theta)
    speedrunvel = speed * cos_theta
    
    # Times correspond to the first point of each interval
    times_out = times[:-1]
    
    return speedrunvel, times_out


def detect_reversals(
    times: np.ndarray,
    speedrunvel: np.ndarray,
    min_duration: float = 3.0
) -> List[Reversal]:
    """
    Detect reverse crawl events from SpeedRunVel time series.
    
    A reversal is defined as a continuous period where SpeedRunVel < 0
    lasting at least min_duration seconds.
    
    Args:
        times: Time array
        speedrunvel: Signed velocity array
        min_duration: Minimum duration for reversal (seconds)
    
    Returns:
        List of Reversal objects
    """
    if len(times) == 0 or len(speedrunvel) == 0:
        return []
    
    reversals = []
    in_reversal = False
    start_idx = None
    start_time = None
    
    for i in range(len(speedrunvel)):
        is_negative = speedrunvel[i] < 0
        
        if is_negative and not in_reversal:
            # Start of reversal
            in_reversal = True
            start_idx = i
            start_time = times[i]
        
        elif not is_negative and in_reversal:
            # End of reversal
            in_reversal = False
            if start_idx is not None:
                duration = times[i] - start_time
                if duration >= min_duration:
                    mean_speed = np.abs(np.mean(speedrunvel[start_idx:i]))
                    reversals.append(Reversal(
                        start_idx=start_idx,
                        end_idx=i - 1,
                        start_time=start_time,
                        end_time=times[i - 1],
                        duration=duration,
                        mean_speed=mean_speed
                    ))
            start_idx = None
    
    # Handle reversal extending to end of data
    if in_reversal and start_idx is not None:
        duration = times[-1] - start_time
        if duration >= min_duration:
            mean_speed = np.abs(np.mean(speedrunvel[start_idx:]))
            reversals.append(Reversal(
                start_idx=start_idx,
                end_idx=len(speedrunvel) - 1,
                start_time=start_time,
                end_time=times[-1],
                duration=duration,
                mean_speed=mean_speed
            ))
    
    return reversals


def detect_turn_events(
    times: np.ndarray,
    head_unit_vec: np.ndarray,
    angle_threshold: float = 45.0,
    min_frames: int = 3
) -> List[TurnEvent]:
    """
    Detect turn/reorientation events from heading angle changes.
    
    A turn is detected when the cumulative heading angle change
    exceeds the threshold within a window.
    
    Args:
        times: Time array
        head_unit_vec: Normalized heading vectors (2, N)
        angle_threshold: Minimum angle change (degrees)
        min_frames: Minimum frames to detect turn
    
    Returns:
        List of TurnEvent objects
    """
    if head_unit_vec.shape[1] < min_frames:
        return []
    
    # Compute heading angles
    angles = np.arctan2(head_unit_vec[1, :], head_unit_vec[0, :])
    
    # Compute angle changes (unwrap to handle -pi to pi discontinuity)
    angle_diff = np.diff(np.unwrap(angles))
    angle_diff_deg = np.rad2deg(angle_diff)
    
    turn_events = []
    i = 0
    
    while i < len(angle_diff) - min_frames:
        # Look for cumulative angle change exceeding threshold
        cumsum = 0.0
        for j in range(i, min(i + 30, len(angle_diff))):  # Max 30 frame window
            cumsum += angle_diff_deg[j]
            
            if abs(cumsum) >= angle_threshold:
                direction = 'left' if cumsum > 0 else 'right'
                turn_events.append(TurnEvent(
                    idx=i,
                    time=times[i],
                    angle_change=abs(cumsum),
                    direction=direction
                ))
                i = j + min_frames  # Skip ahead to avoid double-counting
                break
        else:
            i += 1
    
    return turn_events


def load_track_from_h5(h5_file: h5py.File, track_key: str) -> Optional[Dict]:
    """
    Load track data from H5 file.
    
    Args:
        h5_file: Open H5 file handle
        track_key: Track key (e.g., 'track_001')
    
    Returns:
        Dictionary with track data or None if loading fails
    """
    try:
        track_group = h5_file[f'tracks/{track_key}']
        
        # Load derived quantities
        dq = track_group['derived_quantities']
        shead = dq['shead'][:]
        smid = dq['smid'][:]
        
        # Load SMOOTHED location (sloc) - NOT raw location (points/loc)
        # Must match MATLAB's getDerivedQuantity('sloc')
        if 'sloc' in dq:
            loc = dq['sloc'][:]
        else:
            # Fallback to raw location if sloc not available
            loc = track_group['points']['loc'][:]
        
        # Get time from track-level first (preferred), then root ETI
        if 'eti' in dq:
            eti = dq['eti'][:]
        elif 'eti' in h5_file:
            eti = h5_file['eti'][:]
        else:
            return None
        
        # Get length per pixel - check root first (primary), then metadata (backup)
        length_per_pixel = 0.01  # default
        if 'lengthPerPixel' in h5_file:
            length_per_pixel = float(h5_file['lengthPerPixel'][()])
        elif 'metadata' in h5_file:
            if 'lengthPerPixel' in h5_file['metadata'].attrs:
                length_per_pixel = float(h5_file['metadata'].attrs['lengthPerPixel'])
        
        return {
            'shead': shead,
            'smid': smid,
            'loc': loc,
            'eti': eti,
            'length_per_pixel': length_per_pixel
        }
    
    except Exception as e:
        print(f"Error loading track {track_key}: {e}")
        return None


def analyze_track(track_data: Dict, track_num: int) -> TrackAnalysis:
    """
    Perform full analysis on a single track.
    
    Args:
        track_data: Dictionary with shead, smid, loc, eti, length_per_pixel
        track_num: Track number for identification
    
    Returns:
        TrackAnalysis object with all computed metrics
    """
    shead = track_data['shead']
    smid = track_data['smid']
    loc = track_data['loc']
    eti = track_data['eti']
    length_per_pixel = track_data['length_per_pixel']
    
    # Ensure loc is the right shape
    if loc.shape[0] == 2:
        xpos = loc[0, :]
        ypos = loc[1, :]
    else:
        xpos = loc[:, 0]
        ypos = loc[:, 1]
    
    # Compute SpeedRunVel
    speedrunvel, times = compute_speedrunvel(
        shead, smid, xpos, ypos, eti, length_per_pixel
    )
    
    # Detect reversals
    reversals = detect_reversals(times, speedrunvel, min_duration=3.0)
    
    # Compute heading unit vectors for turn detection
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    
    # Detect turn events
    turn_events = detect_turn_events(times, head_unit_vec, angle_threshold=45.0)
    
    # Compute aggregate statistics
    total_duration = eti[-1] - eti[0] if len(eti) > 1 else 0.0
    mean_speed = np.mean(np.abs(speedrunvel)) if len(speedrunvel) > 0 else 0.0
    mean_speedrunvel = np.mean(speedrunvel) if len(speedrunvel) > 0 else 0.0
    
    # Fraction of time spent reversing
    reversing_frames = np.sum(speedrunvel < 0)
    fraction_reversing = reversing_frames / len(speedrunvel) if len(speedrunvel) > 0 else 0.0
    
    return TrackAnalysis(
        track_num=track_num,
        total_duration=total_duration,
        reversals=reversals,
        turn_events=turn_events,
        mean_speed=mean_speed,
        mean_speedrunvel=mean_speedrunvel,
        fraction_reversing=fraction_reversing
    )


def analyze_h5_file(h5_path: Path) -> Dict:
    """
    Analyze all tracks in an H5 file.
    
    Args:
        h5_path: Path to H5 file
    
    Returns:
        Dictionary with analysis results
    """
    results = {
        'file': str(h5_path),
        'timestamp': datetime.now().isoformat(),
        'tracks': [],
        'summary': {}
    }
    
    with h5py.File(str(h5_path), 'r') as f:
        # Find all tracks
        if 'tracks' not in f:
            print(f"No tracks group in {h5_path}")
            return results
        
        track_keys = list(f['tracks'].keys())
        print(f"Found {len(track_keys)} tracks in {h5_path.name}")
        
        track_analyses = []
        
        for i, track_key in enumerate(track_keys):
            track_data = load_track_from_h5(f, track_key)
            if track_data is None:
                continue
            
            # Extract track number from key
            try:
                track_num = int(track_key.replace('track_', '').replace('track', ''))
            except:
                track_num = i + 1
            
            analysis = analyze_track(track_data, track_num)
            track_analyses.append(analysis)
            
            if analysis.num_reversals > 0:
                print(f"  Track {track_num}: {analysis.num_reversals} reversals, "
                      f"{len(analysis.turn_events)} turns, "
                      f"turn rate: {analysis.turn_rate:.2f}/min")
        
        # Convert to dictionaries
        results['tracks'] = [ta.to_dict() for ta in track_analyses]
        
        # Compute summary statistics
        if track_analyses:
            results['summary'] = compute_summary_statistics(track_analyses)
    
    return results


def compute_summary_statistics(track_analyses: List[TrackAnalysis]) -> Dict:
    """
    Compute population-level summary statistics.
    
    Args:
        track_analyses: List of TrackAnalysis objects
    
    Returns:
        Dictionary with summary statistics
    """
    total_tracks = len(track_analyses)
    tracks_with_reversals = sum(1 for ta in track_analyses if ta.num_reversals > 0)
    
    all_reversals = [r for ta in track_analyses for r in ta.reversals]
    all_durations = [r.duration for r in all_reversals]
    
    all_turn_rates = [ta.turn_rate for ta in track_analyses]
    all_fractions_reversing = [ta.fraction_reversing for ta in track_analyses]
    
    summary = {
        'total_tracks': total_tracks,
        'tracks_with_reversals': tracks_with_reversals,
        'percent_tracks_with_reversals': 100.0 * tracks_with_reversals / total_tracks if total_tracks > 0 else 0.0,
        'total_reversal_events': len(all_reversals),
        'reversal_duration_stats': {
            'mean': np.mean(all_durations) if all_durations else 0.0,
            'median': np.median(all_durations) if all_durations else 0.0,
            'min': np.min(all_durations) if all_durations else 0.0,
            'max': np.max(all_durations) if all_durations else 0.0,
            'std': np.std(all_durations) if all_durations else 0.0
        },
        'turn_rate_stats': {
            'mean': np.mean(all_turn_rates) if all_turn_rates else 0.0,
            'median': np.median(all_turn_rates) if all_turn_rates else 0.0,
            'min': np.min(all_turn_rates) if all_turn_rates else 0.0,
            'max': np.max(all_turn_rates) if all_turn_rates else 0.0,
            'std': np.std(all_turn_rates) if all_turn_rates else 0.0
        },
        'fraction_reversing_stats': {
            'mean': np.mean(all_fractions_reversing) if all_fractions_reversing else 0.0,
            'median': np.median(all_fractions_reversing) if all_fractions_reversing else 0.0,
            'std': np.std(all_fractions_reversing) if all_fractions_reversing else 0.0
        }
    }
    
    return summary


def process_directory(input_dir: Path, output_dir: Optional[Path] = None) -> Dict:
    """
    Process all H5 files in a directory.
    
    Args:
        input_dir: Directory containing H5 files
        output_dir: Optional output directory for JSON results
    
    Returns:
        Combined results dictionary
    """
    input_dir = Path(input_dir)
    h5_files = list(input_dir.glob('**/*.h5'))
    
    print(f"Found {len(h5_files)} H5 files in {input_dir}")
    
    all_results = {
        'processed_at': datetime.now().isoformat(),
        'input_directory': str(input_dir),
        'files': []
    }
    
    for h5_path in h5_files:
        print(f"\nProcessing: {h5_path.name}")
        results = analyze_h5_file(h5_path)
        all_results['files'].append(results)
        
        # Save individual file results
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{h5_path.stem}_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  Saved: {output_file}")
    
    # Compute combined summary
    all_track_analyses = []
    for file_results in all_results['files']:
        for track_dict in file_results.get('tracks', []):
            # Reconstruct minimal TrackAnalysis for summary
            ta = TrackAnalysis(
                track_num=track_dict['track_num'],
                total_duration=track_dict['total_duration'],
                mean_speed=track_dict['mean_speed'],
                mean_speedrunvel=track_dict['mean_speedrunvel'],
                fraction_reversing=track_dict['fraction_reversing']
            )
            ta.reversals = [Reversal(**r) for r in track_dict.get('reversals', [])]
            ta.turn_events = [TurnEvent(**t) for t in track_dict.get('turn_events', [])]
            all_track_analyses.append(ta)
    
    if all_track_analyses:
        all_results['combined_summary'] = compute_summary_statistics(all_track_analyses)
    
    # Save combined results
    if output_dir:
        combined_output = output_dir / 'combined_analysis.json'
        with open(combined_output, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved combined results: {combined_output}")
    
    return all_results


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze H5 experiment files for reverse crawl detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python engineer_data.py /path/to/h5_files
  python engineer_data.py /path/to/single_file.h5 -o /path/to/output
  python engineer_data.py /path/to/h5_files --min-duration 5.0
        """
    )
    
    parser.add_argument('input', type=str,
                        help='Input H5 file or directory containing H5 files')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output directory for JSON results')
    parser.add_argument('--min-duration', type=float, default=3.0,
                        help='Minimum reversal duration in seconds (default: 3.0)')
    parser.add_argument('--angle-threshold', type=float, default=45.0,
                        help='Turn detection angle threshold in degrees (default: 45.0)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else input_path.parent / 'analysis_output'
    
    if input_path.is_file() and input_path.suffix == '.h5':
        # Single file
        results = analyze_h5_file(input_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_path.stem}_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved: {output_file}")
        
    elif input_path.is_dir():
        # Directory of files
        results = process_directory(input_path, output_dir)
        
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return 1
    
    # Print summary
    if 'summary' in results:
        summary = results['summary']
        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        print(f"Total tracks: {summary.get('total_tracks', 0)}")
        print(f"Tracks with reversals: {summary.get('tracks_with_reversals', 0)} "
              f"({summary.get('percent_tracks_with_reversals', 0):.1f}%)")
        print(f"Total reversal events: {summary.get('total_reversal_events', 0)}")
        if summary.get('reversal_duration_stats'):
            dur = summary['reversal_duration_stats']
            print(f"Reversal duration: {dur['mean']:.2f} ± {dur['std']:.2f} s "
                  f"(range: {dur['min']:.2f} - {dur['max']:.2f} s)")
        if summary.get('turn_rate_stats'):
            tr = summary['turn_rate_stats']
            print(f"Turn rate: {tr['mean']:.2f} ± {tr['std']:.2f} turns/min")
    
    return 0


if __name__ == '__main__':
    exit(main())

