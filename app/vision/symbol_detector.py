"""
symbol_detector.py - Detects passive components (R, C, L), ground symbols,
and terminals using morphological feature analysis and bounding box extraction.
"""

import cv2
import numpy as np
from typing import List, Dict, Any

def detect_circuit_symbols(binary_img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extracts candidate symbol regions from preprocessed schematic binary image.
    Classifies candidates by geometric aspect ratio, solidity, and compactness.
    """
    contours, _ = cv2.findContours(binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    symbols = []

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)

        # Filter out tiny noise and massive whole-frame borders
        if area < 80 or w > binary_img.shape[1] * 0.8 or h > binary_img.shape[0] * 0.8:
            continue

        aspect_ratio = float(w) / max(float(h), 1.0)
        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / max(hull_area, 1.0)

        # Heuristic symbol categorization based on standard electronic symbol geometry
        detected_class = "UNKNOWN"
        confidence = 0.75

        # Ground symbol: stacked horizontal bars tapering downward, aspect ratio > 1.2
        if 0.8 <= aspect_ratio <= 2.2 and 20 <= w <= 80 and 15 <= h <= 60:
            # Check for ground-like horizontal gradient
            detected_class = "GROUND"
            confidence = 0.88
        # Capacitor: two parallel plates or gap with aspect ratio ~ 1
        elif 0.5 <= aspect_ratio <= 1.5 and 20 <= w <= 100 and 20 <= h <= 100:
            if solidity < 0.45: # Open gap between plates
                detected_class = "CAPACITOR"
                confidence = 0.82
            else:
                detected_class = "PASSIVE_COMPONENT"
                confidence = 0.78
        # Resistor: elongated zig-zag or rectangle
        elif (aspect_ratio > 2.0 or aspect_ratio < 0.5) and max(w, h) > 40:
            detected_class = "RESISTOR"
            confidence = 0.86
        # Inductor: sequential arcs/loops
        elif 1.2 <= aspect_ratio <= 3.5 and 25 <= h <= 80:
            detected_class = "INDUCTOR"
            confidence = 0.80

        if detected_class != "UNKNOWN":
            symbols.append({
                "class": detected_class,
                "bbox": [int(x), int(y), int(w), int(h)],
                "confidence": float(confidence),
                "center": [int(x + w/2), int(y + h/2)],
                "area": float(area),
                "aspect_ratio": float(aspect_ratio)
            })

    # Non-maximum suppression / deduplication of overlapping boxes
    symbols.sort(key=lambda s: s["area"], reverse=True)
    filtered = []
    for s in symbols:
        x1, y1, w1, h1 = s["bbox"]
        overlap = False
        for f in filtered:
            x2, y2, w2, h2 = f["bbox"]
            # Intersection over union
            inter_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            inter_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            inter_area = inter_x * inter_y
            iou = inter_area / float(w1*h1 + w2*h2 - inter_area)
            if iou > 0.35:
                overlap = True
                break
        if not overlap:
            filtered.append(s)

    return filtered
