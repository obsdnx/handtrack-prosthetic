"""Tests for landmark pre-processing functions in app.py."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import pre_process_landmark, pre_process_point_history, select_mode
import numpy as np


# --- pre_process_landmark ---

def _flat_hand():
    """21 landmarks in a flat horizontal line, all at y=100."""
    return [[i * 10, 100] for i in range(21)]


def test_landmark_output_length():
    pts = _flat_hand()
    result = pre_process_landmark(pts)
    assert len(result) == 42  # 21 landmarks * 2 coords


def test_landmark_normalized_to_minus1_plus1():
    pts = _flat_hand()
    result = pre_process_landmark(pts)
    assert max(map(abs, result)) <= 1.0


def test_landmark_first_point_is_origin():
    pts = _flat_hand()
    result = pre_process_landmark(pts)
    # After relative transform, landmark 0 is (0, 0)
    assert result[0] == 0.0
    assert result[1] == 0.0


def test_landmark_invariant_to_translation():
    pts_a = [[x + 500, y + 300] for x, y in _flat_hand()]
    pts_b = [[x, y] for x, y in _flat_hand()]
    result_a = pre_process_landmark(pts_a)
    result_b = pre_process_landmark(pts_b)
    assert result_a == result_b


# --- pre_process_point_history ---

def _dummy_image():
    return np.zeros((540, 960, 3), dtype=np.uint8)


def test_point_history_empty():
    result = pre_process_point_history(_dummy_image(), [])
    assert result == []


def test_point_history_output_length():
    history = [[100, 200], [110, 210], [120, 220], [130, 230]]
    result = pre_process_point_history(_dummy_image(), history)
    assert len(result) == len(history) * 2


def test_point_history_first_point_is_origin():
    history = [[100, 200], [110, 210]]
    result = pre_process_point_history(_dummy_image(), history)
    assert result[0] == 0.0
    assert result[1] == 0.0


def test_point_history_normalized_by_image_size():
    img = _dummy_image()
    h, w = img.shape[:2]
    history = [[0, 0], [w, h]]
    result = pre_process_point_history(img, history)
    # second point relative to first: (w/w, h/h) = (1.0, 1.0)
    assert abs(result[2] - 1.0) < 1e-6
    assert abs(result[3] - 1.0) < 1e-6


# --- select_mode ---

def test_select_mode_n_resets_to_0():
    _, mode = select_mode(ord("n"), 2)
    assert mode == 0


def test_select_mode_k_sets_1():
    _, mode = select_mode(ord("k"), 0)
    assert mode == 1


def test_select_mode_h_sets_2():
    _, mode = select_mode(ord("h"), 0)
    assert mode == 2


def test_select_mode_digit_sets_number():
    number, _ = select_mode(ord("5"), 0)
    assert number == 5


def test_select_mode_non_digit_returns_minus1():
    number, _ = select_mode(ord("z"), 0)
    assert number == -1


def test_select_mode_unknown_key_preserves_mode():
    _, mode = select_mode(ord("z"), 1)
    assert mode == 1
