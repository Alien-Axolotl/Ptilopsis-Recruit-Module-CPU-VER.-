import threading

import cv2
import mss
import numpy as np
from fastapi import APIRouter
from Engine.ocr_engine import extract_tags
from Engine.find_best import find_best_combination


router = APIRouter()

scan_lock = threading.Lock()
last_result = {"status": "ok", "stars": None, "best_combination": None}

@router.get("/scan")
def scan():
    global last_result

    if not scan_lock.acquire(blocking=False):
        with scan_lock:
            return last_result

    try:
        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[0])
        image = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
        tags = extract_tags(image)
        print("scan result", tags)
        stars, best_combination = find_best_combination(tags)
        print("best result", stars, best_combination)
        last_result = {"status": "ok", "stars": stars, "best_combination": best_combination}
        return last_result
    finally:
        scan_lock.release()
