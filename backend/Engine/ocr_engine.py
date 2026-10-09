
import os
import json
import difflib

import cv2
import numpy as np
import rapidocr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "Data")

#Finds the JSON file that contains the list of tags
TAG_LIST_PATH = os.path.join(DATA_DIR, "tag_list.json")

#Finds the image that has the "Job Tags" template
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "JobTagsTemplate.png")




MIN_MATCH_SCORE = 0.7        
MIN_CONFIDENCE = 0.5           
FUZZY_CUTOFF = 0.8             
EMPTY_BOX_CONTRAST = 15       


PANEL_BRIGHTNESS = 205      
COLORED_SATURATION = 80        
BOX_ASPECT_RANGE = (2.3, 4.5)  
MIN_BOX_HEIGHT = 0.4           
SHADOW_TOLERANCE = 25         

YELLOW_LOWER = (20, 100, 120) 
YELLOW_UPPER = (35, 255, 255)
YELLOW_MIN_RATIO = 0.05




with open(TAG_LIST_PATH, encoding="utf-8") as f:
    TAG_LIST = json.load(f)

TAG_LOOKUP = {tag.lower(): tag for tag in TAG_LIST}

TEMPLATE = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
if TEMPLATE is None:
    raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

reader = rapidocr.RapidOCR(params={"EngineConfig.onnxruntime.intra_op_num_threads": 2})


def best_template_match(gray, scales):
    best = (-1.0, None, None)

    for scale in scales:
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        template = cv2.resize(TEMPLATE, None, fx=scale, fy=scale, interpolation=interpolation)

        too_small = template.shape[0] < 8
        too_big = template.shape[0] >= gray.shape[0] or template.shape[1] >= gray.shape[1]
        if too_small or too_big:
            continue

        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(result)

        if score > best[0]:
            best = (score, location, scale)

    return best


def find_label(gray, min_scale=0.3, max_scale=1.6):
    shrink = min(1.0, 700 / gray.shape[1])
    small = cv2.resize(gray, None, fx=shrink, fy=shrink, interpolation=cv2.INTER_AREA)
    scales = np.linspace(min_scale * shrink, max_scale * shrink, 30)

    score, location, scale = best_template_match(small, scales)
    if location is None:
        return -1.0, None

    scale /= shrink
    x = int(location[0] / shrink)
    y = int(location[1] / shrink)

    template_h, template_w = TEMPLATE.shape
    padding = int(0.1 * template_w * scale) + 10

    left = max(0, x - padding)
    top = max(0, y - padding)
    right = x + int(template_w * scale * 1.1) + padding
    bottom = y + int(template_h * scale * 1.1) + padding
    area = gray[top:bottom, left:right]

    scales = np.linspace(scale * 0.93, scale * 1.07, 15)
    score, location, scale = best_template_match(area, scales)
    if location is None:
        return -1.0, None

    label = (left + location[0], top + location[1], int(template_w * scale), int(template_h * scale))
    return score, label



def search_area(image, label):
    label_x, label_y, label_w, label_h = label
    top = max(0, label_y - 2 * label_h)
    bottom = min(image.shape[0], label_y + 3 * label_h)
    left = label_x + label_w
    return left, top, image[top:bottom, left:]


def box_mask(area, label_h):
    
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    saturation = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)[:, :, 1]
    mask = ((gray < PANEL_BRIGHTNESS) | (saturation > COLORED_SATURATION)).astype(np.uint8) * 255


    size = max(3, label_h // 12)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((size, size), np.uint8))


def trim_shadow(image, box):
    
    x, y, width, height = box
    region = image[y : y + height, x : x + width].astype(int)


    sample = region[height // 4 : height * 3 // 4, width // 10 : width // 5]
    fill_color = np.median(sample.reshape(-1, 3), axis=0)

    matches_fill = np.abs(region - fill_color).max(axis=2) <= SHADOW_TOLERANCE
    rows = np.where(matches_fill.mean(axis=1) > 0.6)[0]
    columns = np.where(matches_fill.mean(axis=0) > 0.6)[0]
    if len(rows) == 0 or len(columns) == 0:
        return box

    return (x + columns[0], y + rows[0], columns[-1] - columns[0] + 1, rows[-1] - rows[0] + 1)


def reading_order(boxes):

    boxes = sorted(boxes, key=lambda box: box[1])
    row_height = np.median([box[3] for box in boxes])

    rows, current_row = [], [boxes[0]]
    for box in boxes[1:]:
        if box[1] - current_row[0][1] < row_height / 2:
            current_row.append(box)
        else:
            rows.append(current_row)
            current_row = [box]
    rows.append(current_row)

    return [box for row in rows for box in sorted(row, key=lambda box: box[0])]


def find_boxes(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    score, label = find_label(gray)
    if score < MIN_MATCH_SCORE:
        return None

    label_h = label[3]
    left, top, area = search_area(image, label)
    contours, _ = cv2.findContours(box_mask(area, label_h), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        aspect = width / height
        is_box_shaped = BOX_ASPECT_RANGE[0] < aspect < BOX_ASPECT_RANGE[1]
        is_big_enough = height > MIN_BOX_HEIGHT * label_h
        is_solid = cv2.contourArea(contour) > 0.8 * width * height  

        if is_box_shaped and is_big_enough and is_solid:
            boxes.append(trim_shadow(image, (x + left, y + top, width, height)))

    if not boxes:
        return None

    
    median_height = np.median([box[3] for box in boxes])
    boxes = [box for box in boxes if abs(box[3] - median_height) < 0.25 * median_height]

    return reading_order(boxes)


def crop_box(image, box, margin_ratio=0.12):
    x, y, width, height = map(int, box)
    margin = int(height * margin_ratio)
    return image[y + margin : y + height - margin, x + margin : x + width - margin]


def is_empty(region):
    return cv2.cvtColor(region, cv2.COLOR_BGR2GRAY).std() < EMPTY_BOX_CONTRAST

#is yellow and has top are used to determine if the tag is a senior operator or top operator. If it is yellow and has top, it is a top operator. If it is yellow and does not have top, it is a senior operator. If it is not yellow, it will be matched to the tag list.
def is_yellow(region):
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, YELLOW_LOWER, YELLOW_UPPER)
    return mask.mean() / 255 >= YELLOW_MIN_RATIO

def has_top(text):
    words = text.lower().split()
    return bool(difflib.get_close_matches("top", words, n=1, cutoff=FUZZY_CUTOFF))


def match_tag(text):
    matches = difflib.get_close_matches(text.strip().lower(), TAG_LOOKUP.keys(), n=1, cutoff=FUZZY_CUTOFF)
    return TAG_LOOKUP[matches[0]] if matches else None


def read_text(region):
    scale = 64 / region.shape[0]
    region = cv2.resize(region, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    result = reader(region, use_det=False, use_cls=False, use_rec=True)
    texts = result.txts or ()
    return " ".join(texts)

def read_box(image, box):
    region = crop_box(image, box)
    if region.size == 0 or is_empty(region):
        return None

    text = read_text(region)
    
    if is_yellow(region):
        if has_top(text):
            return "top-operator"
        return "senior-operator"
    
    
    return match_tag(text)

#extracts tags and returns them in a list
def extract_tags(image):
    if isinstance(image, str):
        image = cv2.imread(image)

    boxes = find_boxes(image)
    if boxes is None:
        return []

    tags = []
    for box in boxes:
        tag = read_box(image, box)
        if tag and tag not in tags:
            tags.append(tag)
    return tags