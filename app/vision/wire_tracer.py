"""
wire_tracer.py - Traces electrical wires, detects junction dots, and identifies connectivity nets.
Separates wire crossings without junction dots from genuine electrical connections.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Any

def detect_junction_dots(binary_img: np.ndarray, min_radius: int = 3, max_radius: int = 15) -> List[Dict[str, Any]]:
    """
    Detects solid circular junction dots connecting wires in the schematic.
    Uses HoughCircles and contour circularity filtering.
    """
    # Junction dots are solid circular connected components
    contours, _ = cv2.findContours(binary_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    junctions = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < 15 or area > 500:
            continue
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        if circularity > 0.65: # Round dot
            (x, y), radius = cv2.minEnclosingCircle(c)
            if min_radius <= radius <= max_radius:
                junctions.append({
                    "x": int(x),
                    "y": int(y),
                    "radius": float(radius),
                    "type": "junction_dot",
                    "confidence": float(circularity)
                })

    return junctions


def trace_wire_segments(binary_img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detects orthogonal and horizontal wire segments using morphological line filters
    and probabilistic Hough Transform.
    """
    h, w = binary_img.shape

    # Extract horizontal lines
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    h_lines_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, h_kernel)

    # Extract vertical lines
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    v_lines_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, v_kernel)

    wire_mask = cv2.bitwise_or(h_lines_img, v_lines_img)

    lines = cv2.HoughLinesP(
        wire_mask,
        rho=1,
        theta=np.pi / 180,
        threshold=40,
        minLineLength=30,
        maxLineGap=10
    )

    segments = []
    if lines is not None:
        for line in lines:
            pts = line.reshape(-1)
            if len(pts) >= 4:
                x1, y1, x2, y2 = int(pts[0]), int(pts[1]), int(pts[2]), int(pts[3])
                orientation = "horizontal" if abs(y2 - y1) < abs(x2 - x1) else "vertical"
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                segments.append({
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "orientation": orientation,
                    "length": float(length)
                })

    return segments
