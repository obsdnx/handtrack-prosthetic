"""Tests for TFLite classifiers — runs real models with synthetic inputs."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from model import KeyPointClassifier, PointHistoryClassifier


def is_int(v):
    return isinstance(v, (int, np.integer))


class TestKeyPointClassifier:
    def setup_method(self):
        self.clf = KeyPointClassifier()

    def test_returns_valid_class_id(self):
        landmarks = [0.0] * 42
        result = self.clf(landmarks)
        assert is_int(result)
        assert 0 <= result <= 9

    def test_open_hand_like_input(self):
        landmarks = [float(i) / 42 for i in range(42)]
        result = self.clf(landmarks)
        assert is_int(result)

    def test_closed_hand_like_input(self):
        landmarks = [0.01 * (i % 2) for i in range(42)]
        result = self.clf(landmarks)
        assert is_int(result)

    def test_deterministic(self):
        landmarks = [float(i % 5) / 5 for i in range(42)]
        assert self.clf(landmarks) == self.clf(landmarks)


class TestPointHistoryClassifier:
    def setup_method(self):
        self.clf = PointHistoryClassifier()

    def test_returns_valid_class_id(self):
        history = [0.0] * 32
        result = self.clf(history)
        assert is_int(result)

    def test_stationary_gesture(self):
        # No movement — all zeros → should classify as stationary (class 0)
        history = [0.0] * 32
        result = self.clf(history)
        assert result == 0

    def test_deterministic(self):
        history = [float(i % 3) / 3 for i in range(32)]
        assert self.clf(history) == self.clf(history)
