#!/usr/bin/env python
import csv
import copy
import argparse
import itertools
import sys
from collections import Counter, deque

import cv2 as cv
import numpy as np
import mediapipe as mp

from utils import CvFpsCalc
from model import KeyPointClassifier, PointHistoryClassifier
from prosthetic.serial_controller import ArduinoController, list_ports
from prosthetic.recorder import GestureRecorder

FINGERTIP_INDICES = {4, 8, 12, 16, 20}

HAND_CONNECTIONS = [
    (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 1), (1, 2), (2, 5), (5, 9), (9, 13), (13, 17), (17, 0),
]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--use_static_image_mode", action="store_true")
    parser.add_argument("--min_detection_confidence", type=float, default=0.7)
    parser.add_argument("--min_tracking_confidence", type=float, default=0.5)
    # Arduino
    parser.add_argument("--arduino", type=str, default=None,
                        help="Serial port for Arduino (e.g. /dev/cu.usbmodem14101). "
                             "Use --list-ports to discover available ports.")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print Arduino commands without sending (no hardware needed)")
    parser.add_argument("--list-ports", action="store_true",
                        help="List available serial ports and exit")
    # Recording
    parser.add_argument("--record", action="store_true",
                        help="Record gesture session to recordings/")
    return parser.parse_args()


def main():
    args = get_args()

    if args.list_ports:
        ports = list_ports()
        if ports:
            print("Available serial ports:")
            for p in ports:
                print(f"  {p}")
        else:
            print("No serial ports found.")
        return

    arduino = None
    if args.arduino or args.dry_run:
        port = args.arduino or "DRY_RUN"
        arduino = ArduinoController(
            port=port,
            baud=115200,
            dry_run=args.dry_run,
        )
        arduino.connect()

    recorder = None
    if args.record:
        recorder = GestureRecorder()
        recorder.start()

    cap = cv.VideoCapture(args.device)
    if not cap.isOpened():
        print(
            f"Error: could not open camera device {args.device}.\n"
            "On macOS, grant camera access to Terminal in:\n"
            "  System Settings → Privacy & Security → Camera",
            file=sys.stderr,
        )
        sys.exit(1)

    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    hands = mp.solutions.hands.Hands(
        static_image_mode=args.use_static_image_mode,
        max_num_hands=1,
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
    )

    keypoint_classifier = KeyPointClassifier()
    point_history_classifier = PointHistoryClassifier()

    keypoint_labels = _load_labels(
        "model/keypoint_classifier/keypoint_classifier_label.csv"
    )
    point_history_labels = _load_labels(
        "model/point_history_classifier/point_history_classifier_label.csv"
    )

    fps_calc = CvFpsCalc(buffer_len=10)

    history_length = 16
    point_history = deque(maxlen=history_length)
    finger_gesture_history = deque(maxlen=history_length)
    mode = 0

    try:
        while True:
            fps = fps_calc.get()
            key = cv.waitKey(10)
            if key == 27:  # ESC
                break
            number, mode = select_mode(key, mode)

            ret, image = cap.read()
            if not ret:
                break

            image = cv.flip(image, 1)
            debug_image = copy.deepcopy(image)

            rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks, results.multi_handedness
                ):
                    brect = calc_bounding_rect(debug_image, hand_landmarks)
                    landmark_list = calc_landmark_list(debug_image, hand_landmarks)

                    pre_landmarks = pre_process_landmark(landmark_list)
                    pre_point_history = pre_process_point_history(debug_image, point_history)

                    logging_csv(number, mode, pre_landmarks, pre_point_history)

                    hand_sign_id = keypoint_classifier(pre_landmarks)
                    if hand_sign_id == 2:  # pointing gesture tracks index fingertip
                        point_history.append(landmark_list[8])
                    else:
                        point_history.append([0, 0])

                    finger_gesture_id = 0
                    if len(pre_point_history) == history_length * 2:
                        finger_gesture_id = point_history_classifier(pre_point_history)

                    finger_gesture_history.append(finger_gesture_id)
                    most_common_fg_id = Counter(finger_gesture_history).most_common()[0][0]

                    # Arduino output — stream angles directly from landmarks
                    if arduino:
                        arduino.send_frame(landmark_list)

                    # Recording
                    if recorder:
                        recorder.record(
                            gesture_id=int(hand_sign_id),
                            gesture_label=keypoint_labels[hand_sign_id],
                            motion_id=int(most_common_fg_id),
                            motion_label=point_history_labels[most_common_fg_id],
                            landmark_list=landmark_list,
                        )

                    debug_image = draw_bounding_rect(debug_image, brect)
                    debug_image = draw_landmarks(debug_image, landmark_list)
                    debug_image = draw_info_text(
                        debug_image,
                        brect,
                        handedness,
                        keypoint_labels[hand_sign_id],
                        point_history_labels[most_common_fg_id],
                    )
            else:
                point_history.append([0, 0])
                if arduino:
                    arduino.send_idle()

            debug_image = draw_point_history(debug_image, point_history)
            debug_image = draw_info(debug_image, fps, mode, number)

            cv.imshow("Hand Gesture Recognition", debug_image)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv.destroyAllWindows()
        if recorder:
            recorder.stop()
        if arduino:
            arduino.disconnect()


def _load_labels(path):
    with open(path, encoding="utf-8-sig") as f:
        return [row[0] for row in csv.reader(f)]


def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:
        number = key - 48
    if key == ord("n"):
        mode = 0
    if key == ord("k"):
        mode = 1
    if key == ord("h"):
        mode = 2
    return number, mode


def calc_bounding_rect(image, landmarks):
    h, w = image.shape[:2]
    points = np.array(
        [
            [min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
            for lm in landmarks.landmark
        ],
        dtype=int,
    )
    x, y, bw, bh = cv.boundingRect(points)
    return [x, y, x + bw, y + bh]


def calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    return [
        [min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
        for lm in landmarks.landmark
    ]


def pre_process_landmark(landmark_list):
    pts = copy.deepcopy(landmark_list)
    base_x, base_y = pts[0]
    for pt in pts:
        pt[0] -= base_x
        pt[1] -= base_y
    flat = list(itertools.chain.from_iterable(pts))
    max_val = max(map(abs, flat))
    return [v / max_val for v in flat]


def pre_process_point_history(image, point_history):
    h, w = image.shape[:2]
    pts = copy.deepcopy(point_history)
    if not pts:
        return []
    base_x, base_y = pts[0]
    normalized = [
        [(p[0] - base_x) / w, (p[1] - base_y) / h]
        for p in pts
    ]
    return list(itertools.chain.from_iterable(normalized))


def logging_csv(number, mode, landmark_list, point_history_list):
    if mode == 1 and 0 <= number <= 9:
        with open("model/keypoint_classifier/keypoint.csv", "a", newline="") as f:
            csv.writer(f).writerow([number, *landmark_list])
    if mode == 2 and 0 <= number <= 9:
        with open(
            "model/point_history_classifier/point_history.csv", "a", newline=""
        ) as f:
            csv.writer(f).writerow([number, *point_history_list])


def draw_landmarks(image, landmark_point):
    if not landmark_point:
        return image

    for start, end in HAND_CONNECTIONS:
        cv.line(image, tuple(landmark_point[start]), tuple(landmark_point[end]), (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[start]), tuple(landmark_point[end]), (255, 255, 255), 2)

    for index, pt in enumerate(landmark_point):
        radius = 8 if index in FINGERTIP_INDICES else 5
        cv.circle(image, tuple(pt), radius, (255, 255, 255), -1)
        cv.circle(image, tuple(pt), radius, (0, 0, 0), 1)

    return image


def draw_bounding_rect(image, brect):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]), (0, 0, 0), 1)
    return image


def draw_info_text(image, brect, handedness, hand_sign_text, finger_gesture_text):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)

    label = handedness.classification[0].label
    if hand_sign_text:
        label += ":" + hand_sign_text
    cv.putText(image, label, (brect[0] + 5, brect[1] - 4),
               cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

    if finger_gesture_text:
        text = "Finger Gesture:" + finger_gesture_text
        cv.putText(image, text, (10, 60), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(image, text, (10, 60), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)

    return image


def draw_point_history(image, point_history):
    for index, point in enumerate(point_history):
        if point[0] != 0 and point[1] != 0:
            cv.circle(image, (point[0], point[1]), 1 + index // 2, (152, 251, 152), 2)
    return image


def draw_info(image, fps, mode, number):
    cv.putText(image, f"FPS:{fps}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
    cv.putText(image, f"FPS:{fps}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)

    mode_labels = {1: "Logging Key Point", 2: "Logging Point History"}
    if mode in mode_labels:
        cv.putText(image, f"MODE:{mode_labels[mode]}", (10, 90),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        if 0 <= number <= 9:
            cv.putText(image, f"NUM:{number}", (10, 110),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

    return image


if __name__ == "__main__":
    main()
