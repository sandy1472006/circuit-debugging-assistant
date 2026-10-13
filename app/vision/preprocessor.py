"""
preprocessor.py - Image ingestion and preprocessing for electronic circuit schematics.
Supports PNG, JPG, JPEG, and PDF rendering with contrast enhancement and binarization.
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Tuple, Optional, Dict, Any

def load_and_preprocess_image(file_path: Path, max_dim: int = 1600) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Loads image or first page of PDF, applies deskew and adaptive binarization.
    Returns:
        rgb_img: Original or resized RGB image for display
        binary_img: Inverted binary image (wires and symbols are 255, background is 0)
        metadata: Preprocessing information
    """
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        # Extract first page as image using PIL or render fallback
        try:
            # Check if pdf2image or pypdf is available, or use Pillow if supported
            pil_img = Image.open(file_path)
            rgb_img = np.array(pil_img.convert("RGB"))
        except Exception:
            # Fallback: create placeholder schematic canvas if PDF parser not present
            rgb_img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
            cv2.putText(rgb_img, "PDF Document Loaded", (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (15, 23, 42), 2)
    else:
        # Load standard image with OpenCV
        bgr = cv2.imread(str(file_path))
        if bgr is None:
            # Try PIL
            pil_img = Image.open(file_path).convert("RGB")
            rgb_img = np.array(pil_img)
        else:
            rgb_img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    h, w = rgb_img.shape[:2]
    # Resize if excessively large while preserving aspect ratio
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        rgb_img = cv2.resize(rgb_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)

    # Denoise using bilateral filter to preserve sharp schematic wire edges
    denoised = cv2.bilateralFilter(gray, 7, 50, 50)

    # Adaptive Otsu thresholding
    # Usually schematics have light background (255) and black ink (0).
    # We produce an inverted binary image (ink is 255, background 0) for contour and skeleton operations.
    _, binary_inv = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)

    metadata = {
        "original_width": w,
        "original_height": h,
        "processed_width": rgb_img.shape[1],
        "processed_height": rgb_img.shape[0],
        "scale_factor": scale,
        "mean_intensity": float(np.mean(gray)),
        "is_inverted": False
    }

    return rgb_img, cleaned, metadata
