
import cv2
import numpy as np
import math

# ===============================
# TOOL DETECTION
# ===============================
def detect_tools(frame, model):
    results = model(frame, verbose=False)
    tools = []

    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf > 0.4:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            tools.append({
                "bbox": (x1, y1, x2, y2),
                "confidence": round(conf, 2)
            })
    return tools


# ===============================
# BLOOD DETECTION
# ===============================
def blood_ratio(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask = (
        cv2.inRange(hsv, lower_red1, upper_red1) +
        cv2.inRange(hsv, lower_red2, upper_red2)
    )

    return cv2.countNonZero(mask) / (frame.shape[0] * frame.shape[1])


# ===============================
# SMOKE DETECTION
# ===============================
def preprocess(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (5, 5), 0)

def smoke_score(frame):
    gray = preprocess(frame)
    return np.std(gray)


# ===============================
# HELPERS
# ===============================
def box_center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    return inter / float(areaA + areaB - inter)


# ===============================
# STATE
# ===============================
prev_tools = []


# ===============================
# MAIN PIPELINE
# ===============================
def run_inference(frame, models):
    global prev_tools

    alerts = []

    # Tool detection
    tools = detect_tools(frame, models["tool_model"])

    if tools:
        alerts.append({
            "type": "tool_detected",
            "confidence": max(t["confidence"] for t in tools)
        })

    # Tool-tool collision
    for i in range(len(tools)):
        for j in range(i + 1, len(tools)):
            overlap = iou(tools[i]["bbox"], tools[j]["bbox"])
            if overlap > 0.3:
                alerts.append({
                    "type": "tool_tool_collision",
                    "confidence": round(overlap, 2)
                })

    # Fast tool motion
    if prev_tools:
        for p, c in zip(prev_tools, tools):
            cx1, cy1 = box_center(p["bbox"])
            cx2, cy2 = box_center(c["bbox"])
            speed = math.dist((cx1, cy1), (cx2, cy2))

            if speed > 40:
                alerts.append({
                    "type": "fast_tool_motion",
                    "confidence": round(min(speed / 100, 1.0), 2)
                })

    # Critical region
    h, w = frame.shape[:2]
    critical_box = (
        int(w * 0.2), int(h * 0.2),
        int(w * 0.8), int(h * 0.8)
    )

    for t in tools:
        overlap = iou(t["bbox"], critical_box)
        if overlap > 0.1:
            alerts.append({
                "type": "tool_near_critical_region",
                "confidence": round(overlap, 2)
            })

    # Blood & smoke
    blood = blood_ratio(frame)
    smoke = smoke_score(frame)

    if blood > 0.02:
        alerts.append({
            "type": "blood_detected",
            "confidence": round(blood, 3)
        })

    if smoke < 40:
        alerts.append({
            "type": "smoke_detected",
            "confidence": round(1 - smoke / 100, 2)
        })

    # Visibility
    if smoke < 40 or blood > 0.02:
        visibility = "POOR"
    elif smoke < 60:
        visibility = "MODERATE"
    else:
        visibility = "GOOD"

    prev_tools = tools

    return {
        "visibility": visibility,
        "alerts": alerts
    }
