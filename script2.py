import cv2
import numpy as np
import mediapipe as mp
import json
import os
import hashlib
from typing import List, Dict, Optional, Tuple

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _get_template_id(image_path: str) -> str:
    """Generates a unique MD5 hash for a template image file."""
    with open(image_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def _load_slots_from_json(json_file_path: str) -> Dict:
    """Loads slot coordinates from a JSON file, returning an empty dict on failure."""
    if not os.path.exists(json_file_path):
        return {}
    try:
        with open(json_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save_slots_to_json(slots_data: Dict, json_file_path: str):
    """Saves slot coordinates to a JSON file."""
    try:
        with open(json_file_path, 'w') as f:
            json.dump(slots_data, f, indent=4)
    except IOError as e:
        # In an API context, this should be logged, not printed.
        # For now, we fail silently or let the exception propagate.
        pass

def _detect_circular_slots(image_path: str) -> List[Dict]:
    """Detects circular areas (slots) in a given image."""
    image = cv2.imread(image_path)
    if image is None:
        return []
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    slot_list = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
            
        circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
        
        # Filter for shapes that are sufficiently large and circular.
        if circularity > 0.75 and area > 3000:
            (x_center, y_center), radius = cv2.minEnclosingCircle(contour)
            if radius >= 100:
                slot = {
                    "x": int(x_center - radius),
                    "y": int(y_center - radius),
                    "width": int(radius * 2),
                    "height": int(radius * 2),
                    "center_x": int(x_center),
                    "center_y": int(y_center),
                    "radius": int(radius),
                    "shape": "circle"
                }
                slot_list.append(slot)
    
    return slot_list

def _get_or_detect_slots(template_path: str, slots_json_path: str) -> List[Dict]:
    """
    Retrieves slot coordinates for a template, either from a cache (JSON file)
    or by running new detection.
    """
    template_id = _get_template_id(template_path)
    slots_data = _load_slots_from_json(slots_json_path)
    
    if template_id in slots_data:
        return slots_data[template_id]
    
    # Not found in cache, so detect, save, and return new slots.
    new_slots = _detect_circular_slots(template_path)
    slots_data[template_id] = new_slots
    _save_slots_to_json(slots_data, slots_json_path)
    return new_slots

def _crop_face_for_slot(image_path: str, slot_width: int, slot_height: int) -> Optional[np.ndarray]:
    """Crops a face from an image, centered and resized for a specific slot."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w, _ = img.shape

    # Use MediaPipe for robust face detection.
    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as fd:
        results = fd.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.detections:
            return None

        bbox = results.detections[0].location_data.relative_bounding_box
        x_center = int((bbox.xmin + bbox.width / 2) * w)
        y_center = int((bbox.ymin + bbox.height / 2) * h)

        x1 = max(0, x_center - slot_width // 2)
        y1 = max(0, y_center - slot_height // 2)
        x2 = min(w, x1 + slot_width)
        y2 = min(h, y1 + slot_height)

        crop = img[y1:y2, x1:x2]
        
        # Resize if the crop is smaller than the target slot.
        if crop.shape[0] < slot_height or crop.shape[1] < slot_width:
            crop = cv2.resize(crop, (slot_width, slot_height), interpolation=cv2.INTER_CUBIC)
            
        return crop

def _merge_faces_to_slots(poster_img: np.ndarray, face_images: List[np.ndarray], slots: List[Dict]) -> np.ndarray:
    """Merges cropped face images into the circular slots on a poster."""
    canvas = poster_img.copy()
    
    for face_img, slot in zip(face_images, slots):
        if face_img is None:
            continue
            
        x, y, w, h = slot['x'], slot['y'], slot['width'], slot['height']
        radius = slot['radius']
        
        # Ensure face image matches slot dimensions.
        if face_img.shape[:2] != (h, w):
            face_img = cv2.resize(face_img, (w, h), interpolation=cv2.INTER_CUBIC)
        
        # Create a circular mask to blend the face smoothly.
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (w//2, h//2), radius, 255, -1)
        
        face_masked = cv2.bitwise_and(face_img, face_img, mask=mask)
        
        mask_inv = cv2.bitwise_not(mask)
        poster_region = canvas[y:y+h, x:x+w]
        poster_masked = cv2.bitwise_and(poster_region, poster_region, mask=mask_inv)
        
        combined = cv2.add(face_masked, poster_masked)
        canvas[y:y+h, x:x+w] = combined
        
    return canvas

# ==============================================================================
# MAIN API-FRIENDLY FUNCTION
# ==============================================================================

def populate_poster_slots(
    template_path: str,
    face_image_paths: List[str],
    output_filename: str,
    slots_json_path: str = "template_slots.json"
) -> Optional[str]:
    """
    Detects circular slots in a poster, crops faces, and merges them into the slots.

    This function is designed to be called from an API. It takes paths to a template
    and face images, performs all processing, and saves the final result to a
    dedicated 'outputs' folder.

    Args:
        template_path (str): The file path to the poster template image.
        face_image_paths (List[str]): A list of file paths to the face images to insert.
        output_filename (str): The filename for the final generated image (e.g., "final_poster.png").
        slots_json_path (str): Path to a JSON file for caching detected slot coordinates
                               to speed up subsequent runs with the same template.

    Returns:
        Optional[str]: The full path to the saved output image if successful, otherwise None.
    """
    # --- 1. Inputs and Setup ---
    if not os.path.exists(template_path):
        # In a real API, you would raise a specific HTTP exception.
        return None

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    final_output_path = os.path.join(output_dir, output_filename)

    # --- 2. Processing ---
    # Get or detect slots for the template.
    slots = _get_or_detect_slots(template_path, slots_json_path)
    if not slots:
        # No circular slots detected — preserve the input template (the generated poster)
        # by copying it to the expected output path so styling changes remain visible.
        template_img = cv2.imread(template_path)
        if template_img is None:
            return None
        cv2.imwrite(final_output_path, template_img)
        return final_output_path
    
    # Sort slots by position (top-to-bottom, left-to-right) for predictable ordering.
    sorted_slots = sorted(slots, key=lambda s: (s['y'], s['x']))
    
    # Load the base template image to draw on.
    template_img = cv2.imread(template_path)
    
    # Crop a face for each available slot.
    face_images = []
    num_slots = len(sorted_slots)
    for i, face_path in enumerate(face_image_paths):
        if i >= num_slots:
            break # Stop if we have more faces than slots.
        if not os.path.exists(face_path):
            continue

        slot = sorted_slots[i]
        face_crop = _crop_face_for_slot(face_path, slot['width'], slot['height'])
        face_images.append(face_crop)
    
    # Merge the cropped faces onto the template.
    final_image = _merge_faces_to_slots(template_img, face_images, sorted_slots)
    
    # --- 3. Outputs ---
    # Save the final image to the specified path.
    cv2.imwrite(final_output_path, final_image)
    
    return final_output_path


# ==============================================================================
# EXAMPLE USAGE (for testing purposes)
# ==============================================================================
if __name__ == "__main__":
    # This block will only run when the script is executed directly.
    # It demonstrates how to use the `populate_poster_slots` function.
    
    # Define paths for the template and face images.
    # Ensure these files exist in your project directory.
    TEMPLATE_IMAGE = "assets/2_slot_template.png"
    FACE_IMAGES = ["assets/p1.jpeg"]
    OUTPUT_FILE = "final_poster_with_faces.png"
    SLOT_CACHE_FILE = "template_slots.json"

    print(f"Processing template: {TEMPLATE_IMAGE}")
    print(f"With faces: {FACE_IMAGES}")

    # Call the main function.
    try:
        result_path = populate_poster_slots(
            template_path=TEMPLATE_IMAGE,
            face_image_paths=FACE_IMAGES,
            output_filename=OUTPUT_FILE,
            slots_json_path=SLOT_CACHE_FILE
        )

        if result_path:
            print(f"✅ Success! Final poster saved to: {result_path}")
        else:
            print("❌ Failure. Could not generate poster. Check input files and template content.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")