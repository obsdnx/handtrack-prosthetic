"""
Records gesture sessions to disk for analysis and replay.

Each session is saved as a CSV with columns:
  timestamp, gesture_id, gesture_label, motion_id, motion_label,
  landmark_0_x, landmark_0_y, ..., landmark_20_x, landmark_20_y
"""
import csv
import time
from pathlib import Path
from datetime import datetime


RECORDINGS_DIR = Path("recordings")


class GestureRecorder:
    """
    Records one gesture session to a timestamped CSV file.

    Usage:
        recorder = GestureRecorder()
        recorder.start()
        recorder.record(gesture_id, gesture_label, motion_id, motion_label, landmark_list)
        recorder.stop()   # writes file and prints path
    """

    _LANDMARK_HEADERS = [
        f"landmark_{i}_{axis}" for i in range(21) for axis in ("x", "y")
    ]
    _HEADERS = [
        "timestamp",
        "gesture_id",
        "gesture_label",
        "motion_id",
        "motion_label",
        *_LANDMARK_HEADERS,
    ]

    def __init__(self, output_dir=RECORDINGS_DIR):
        self._output_dir = Path(output_dir)
        self._rows = []
        self._start_time = None
        self._session_file = None
        self.is_recording = False

    def start(self):
        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_file = self._output_dir / f"session_{timestamp}.csv"
        self._rows = []
        self._start_time = time.time()
        self.is_recording = True
        print(f"[Recorder] Started — saving to {self._session_file}")

    def record(self, gesture_id, gesture_label, motion_id, motion_label, landmark_list):
        if not self.is_recording:
            return
        elapsed = round(time.time() - self._start_time, 4)
        flat_landmarks = [coord for pt in landmark_list for coord in pt]
        self._rows.append([elapsed, gesture_id, gesture_label, motion_id, motion_label, *flat_landmarks])

    def stop(self):
        if not self.is_recording:
            return
        self.is_recording = False
        with open(self._session_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self._HEADERS)
            writer.writerows(self._rows)
        print(f"[Recorder] Saved {len(self._rows)} frames → {self._session_file}")
        return self._session_file
