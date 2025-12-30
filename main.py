import cv2
import numpy as np
import matplotlib.pyplot as plt

from visibility import assess_visibility
from safety import (
    detect_tools,
    assess_tool_safety,
    tool_near_critical_region,
    tool_motion_speed,
    draw_critical_region
)

print("Setup complete")

def main():
    cap = cv2.VideoCapture("capture1.avi")

    frame_count = 0
    N = 40
    previous_centers = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

       
        visibility, reasons, confidence = assess_visibility(frame)

        tools = detect_tools(frame)

        safety = assess_tool_safety(tools)

        critical_risk = tool_near_critical_region(tools, frame)

        current_centers, speed_risk = tool_motion_speed(tools, previous_centers)
        previous_centers = current_centers

        color = (0,255,0) if visibility == "GOOD" else \
                (0,165,255) if visibility == "MODERATE" else (0,0,255)

        label = f"Visibility: {visibility}"
        if reasons:
            label += f" ({', '.join(reasons)})"
        label += f" | {confidence}%"

        cv2.putText(frame, label,
                    (30,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, color, 3)

        # Draw tools
        for box in tools:
            cv2.rectangle(frame,
                          (box[0], box[1]),
                          (box[2], box[3]),
                          (255,255,0), 2)
          
        draw_critical_region(frame)

        
        y = 90
        if safety == "RISK":
            cv2.putText(frame, " TOOL COLLISION RISK",
                        (30,y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 3)
            y += 40

        if critical_risk:
            cv2.putText(frame, "TOOL NEAR CRITICAL REGION",
                        (30,y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255,0,255), 3)
            y += 40

        if speed_risk:
            cv2.putText(frame, "FAST TOOL MOVEMENT",
                        (30,y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,140,255), 3)

        if frame_count % N == 0:
            plt.figure(figsize=(5,5))
            plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            plt.axis("off")
            plt.show()

    cap.release()

if __name__ == "__main__":
    main()
