"""Simulates the gesture → prosthetic command pipeline without hardware."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from collections import deque, Counter
from model import KeyPointClassifier, PointHistoryClassifier
from app import pre_process_landmark, pre_process_point_history
import numpy as np

# Placeholder command map — will be replaced once hardware protocol is known
GESTURE_COMMANDS = {
    0: "OPEN_GRIPPER",
    1: "CLOSE_GRIPPER",
    2: "PINCH",
}

MOTION_COMMANDS = {
    0: "HOLD",
    1: "ROTATE_CW",
    2: "ROTATE_CCW",
    3: "MOVE",
}


def gesture_to_command(gesture_id):
    return GESTURE_COMMANDS.get(gesture_id, f"UNKNOWN({gesture_id})")


def motion_to_command(motion_id):
    return MOTION_COMMANDS.get(motion_id, f"UNKNOWN({motion_id})")


class GestureDebouncer:
    """Only emits a command when the same gesture holds for `threshold` frames."""

    def __init__(self, threshold=5):
        self.threshold = threshold
        self._history = deque(maxlen=threshold)
        self._last_sent = None

    def update(self, gesture_id):
        self._history.append(gesture_id)
        if len(self._history) < self.threshold:
            return None
        most_common, count = Counter(self._history).most_common(1)[0]
        if count == self.threshold and most_common != self._last_sent:
            self._last_sent = most_common
            return most_common
        return None


# --- tests ---

class TestCommandMapping:
    def test_known_gestures_map_to_commands(self):
        assert gesture_to_command(0) == "OPEN_GRIPPER"
        assert gesture_to_command(1) == "CLOSE_GRIPPER"
        assert gesture_to_command(2) == "PINCH"

    def test_unknown_gesture_returns_fallback(self):
        assert gesture_to_command(99) == "UNKNOWN(99)"

    def test_motion_commands_map(self):
        assert motion_to_command(0) == "HOLD"
        assert motion_to_command(1) == "ROTATE_CW"
        assert motion_to_command(2) == "ROTATE_CCW"


class TestDebouncer:
    def test_no_output_below_threshold(self):
        d = GestureDebouncer(threshold=5)
        for _ in range(4):
            assert d.update(1) is None

    def test_fires_after_threshold(self):
        d = GestureDebouncer(threshold=5)
        result = None
        for _ in range(5):
            result = d.update(1)
        assert result == 1

    def test_no_repeat_for_same_gesture(self):
        d = GestureDebouncer(threshold=5)
        for _ in range(5):
            d.update(1)
        # Same gesture again — should not fire twice
        for _ in range(5):
            result = d.update(1)
        assert result is None

    def test_fires_on_gesture_change(self):
        d = GestureDebouncer(threshold=3)
        for _ in range(3):
            d.update(0)
        result = None
        for _ in range(3):
            result = d.update(1)
        assert result == 1

    def test_noisy_frames_suppressed(self):
        d = GestureDebouncer(threshold=5)
        # Alternating noisy signal — should never fire
        for i in range(10):
            result = d.update(i % 2)
            assert result is None


class TestFullPipeline:
    """Runs synthetic landmarks through pre-processing + classifier + command mapping."""

    def setup_method(self):
        self.clf = KeyPointClassifier()
        self.debouncer = GestureDebouncer(threshold=5)
        self.img = np.zeros((540, 960, 3), dtype=np.uint8)

    def _make_landmarks(self, spread=1.0):
        """Generate 21 synthetic landmark points."""
        return [[int(i * 10 * spread), 100] for i in range(21)]

    def test_pipeline_produces_command(self):
        landmarks = self._make_landmarks()
        pre = pre_process_landmark(landmarks)
        gesture_id = self.clf(pre)
        command = gesture_to_command(gesture_id)
        assert isinstance(command, str)
        assert len(command) > 0

    def test_stable_gesture_triggers_debounced_command(self):
        landmarks = self._make_landmarks()
        pre = pre_process_landmark(landmarks)
        gesture_id = self.clf(pre)

        fired = []
        for _ in range(10):
            result = self.debouncer.update(gesture_id)
            if result is not None:
                fired.append(gesture_to_command(result))

        assert len(fired) == 1  # debouncer fires exactly once for stable gesture
        print(f"\n  Stable gesture → command: {fired[0]}")
