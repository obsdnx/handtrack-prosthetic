# Hand Gesture Recognition — MediaPipe

Real-time hand sign and finger gesture recognition using MediaPipe and a lightweight MLP classifier.

![demo](https://user-images.githubusercontent.com/37477845/102222442-c452cd00-3f26-11eb-93ec-c387c98231be.gif)

---

## Setup on macOS

### Prerequisites
- Python 3.12 (TensorFlow does not yet support 3.13+)
- A webcam

### Step 1 — Clone the repo

```bash
git clone https://github.com/obsdnx/handtrack-prosthetic.git
cd handtrack-prosthetic/montreal
```

### Step 2 — Create a virtual environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs mediapipe, TensorFlow, and OpenCV. Takes ~2 minutes on first run.

### Step 4 — Grant camera access

macOS blocks camera access by default for terminal apps.

1. Open **System Settings → Privacy & Security → Camera**
2. Enable access for **Terminal** (or iTerm2, whichever you use)
3. If you never saw a permission dialog, reset and re-trigger it:
   ```bash
   tccutil reset Camera
   ```

### Step 5 — Run the app

```bash
open -a Terminal run.sh
```

This opens a new Terminal.app window (which has camera access) and launches the app. A window will appear showing your webcam feed with hand landmarks overlaid.

> If you prefer to run from your own terminal after granting camera access:
> ```bash
> source venv/bin/activate
> python app.py
> ```

### Step 6 — Run the tests

```bash
source venv/bin/activate
pytest tests/ -v
```

All 31 tests should pass. No camera or hardware required.

### Options

| Flag | Default | Description |
|---|---|---|
| `--device` | `0` | Camera device index |
| `--width` | `960` | Capture width |
| `--height` | `540` | Capture height |
| `--use_static_image_mode` | off | Use static image mode (slower but more accurate on stills) |
| `--min_detection_confidence` | `0.7` | Detection confidence threshold |
| `--min_tracking_confidence` | `0.5` | Tracking confidence threshold |

### Keyboard controls

| Key | Action |
|---|---|
| `ESC` | Quit |
| `k` | Enter keypoint logging mode |
| `h` | Enter point history logging mode |
| `n` | Exit logging mode |
| `0`–`9` | Label for the current gesture (while in logging mode) |

---

## Setup with Docker (Linux)

Docker cannot access the macOS camera directly. On **Linux** with a webcam at `/dev/video0`:

```bash
docker build -t hand-gesture .
docker run --rm \
  --device /dev/video0 \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  hand-gesture
```

You may need to allow X11 connections first:
```bash
xhost +local:docker
```

---

## Project structure

```
app.py                              Main inference script
requirements.txt                    Python dependencies
Dockerfile                          Container build file
model/
  keypoint_classifier/
    keypoint_classifier.tflite      Hand sign model
    keypoint_classifier_label.csv   Hand sign labels
    keypoint.csv                    Training data
    keypoint_classifier.py          Inference module
  point_history_classifier/
    point_history_classifier.tflite Finger gesture model
    point_history_classifier_label.csv
    point_history.csv               Training data
    point_history_classifier.py     Inference module
utils/
  cvfpscalc.py                      FPS measurement utility
keypoint_classification_EN.ipynb    Notebook to retrain hand sign model
point_history_classification.ipynb  Notebook to retrain gesture model
```

---

## Training custom gestures

### Collect keypoint data
1. Run the app and press `k` to enter keypoint logging mode
2. Show a gesture and press `0`–`9` to label and save it
3. Data is appended to `model/keypoint_classifier/keypoint.csv`

### Collect point history data
1. Press `h` to enter point history logging mode
2. Perform a motion gesture and press `0`–`9` to label it
3. Data is appended to `model/point_history_classifier/point_history.csv`

### Retrain
Open the relevant notebook and run all cells:
- `keypoint_classification_EN.ipynb` — hand signs
- `point_history_classification.ipynb` — finger gestures

---

## Credits

Original: [Kazuhito Takahashi](https://twitter.com/KzhtTkhs)  
English translation: [Nikita Kiselov](https://github.com/kinivi)

License: [Apache v2](LICENSE)
