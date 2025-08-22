import cv2
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from thefuzz import process
import re
import json
import os
from typing import List, Dict, Tuple, Optional

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_contrasting_color(color: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """
    Calculates whether black or white text is more readable on a given background color.

    This is based on the perceived luminance of the color. A high luminance (bright color)
    gets black text, while a low luminance (dark color) gets white text.

    Args:
        color (Tuple[float, float, float]): An RGB color tuple (e.g., (128, 255, 0)).

    Returns:
        Tuple[int, int, int]: (0, 0, 0) for black or (255, 255, 255) for white.
    """
    # Calculate luminance using the standard formula for sRGB.
    luminance = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]) / 255
    # If luminance is greater than 0.5, the background is light; use black text.
    return (0, 0, 0) if luminance > 0.5 else (255, 255, 255)


def get_wrapped_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """
    Wraps text to fit within a specified width, while respecting manual newlines ('\\n').

    Args:
        text (str): The input text to wrap.
        font (ImageFont.FreeTypeFont): The font object used for measuring text width.
        max_width (int): The maximum width in pixels for a line of text.

    Returns:
        str: The text with newlines inserted for wrapping.
    """
    if max_width <= 0 or not text:
        return text

    all_final_lines = []
    manual_lines = text.split('\\n')

    for line in manual_lines:
        words = line.split()
        if not words:
            all_final_lines.append("")
            continue

        current_line_segment = words[0]
        for word in words[1:]:
            if font.getbbox(current_line_segment + " " + word)[2] <= max_width:
                current_line_segment += " " + word
            else:
                all_final_lines.append(current_line_segment)
                current_line_segment = word
        
        all_final_lines.append(current_line_segment)

    return "\\n".join(all_final_lines)


def create_template_mapping(base_image_path: str, content_keys: List[str]) -> Dict:
    """
    Performs one-time OCR detection to map field keys to bounding boxes on a template.

    Args:
        base_image_path (str): The file path to the template image.
        content_keys (List[str]): A list of strings representing the keys for text fields.

    Returns:
        Dict: A dictionary mapping each key to its bounding box coordinates. Returns
              an empty dictionary if the process fails.
    """
    try:
        image_cv = cv2.imread(base_image_path)
        if image_cv is None:
            raise FileNotFoundError(f"Image not found at {base_image_path}")
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        reader = easyocr.Reader(['en'], gpu=False)
        ocr_results = reader.readtext(image_rgb)
    except Exception as e:
        # Proper error logging should be handled by the calling API.
        # For this module, we return an empty mapping on failure.
        return {}

    mapped_fields = {}
    used_ocr_indices = set()
    
    all_keys = list(content_keys) + ['organisation_logo', 'icon1', 'icon2']
    available_keys = [k for k in all_keys if k not in mapped_fields]

    for i, (bbox, text, _) in enumerate(ocr_results):
        if i in used_ocr_indices:
            continue
        
        clean_text = re.sub(r'[\d\W_]+', '', text).lower()
        if not clean_text:
            continue
            
        match = process.extractOne(clean_text, available_keys, score_cutoff=70)
        
        if match:
            best_match_key = match[0]
            serializable_bbox = [[float(p[0]), float(p[1])] for p in bbox]
            mapped_fields[best_match_key] = {'bbox': serializable_bbox}
            
            used_ocr_indices.add(i)
            available_keys.remove(best_match_key)
            
    return mapped_fields

# ==============================================================================
# MAIN PROCESSING FUNCTION
# ==============================================================================

def generate_poster(
    base_image_path: str,
    text_content: Dict[str, str],
    output_filename: str,
    mapping_json_path: str,
    font_path: str,
    logo_paths: Optional[List[str]] = None,
    font_sizes: Optional[Dict[str, int]] = None,
    custom_colors: Optional[Dict[str, str]] = None,
    logo_scale: float = 1.0,
    venue_icon_path: Optional[str] = None,
    calendar_icon_path: Optional[str] = None,
    icon_scale: float = 1.0
) -> str:
    """
    Generates a poster by dynamically placing text, logos, and icons onto a base image.

    This function is designed to be called from an API. It takes all necessary paths
    and content as arguments, processes the image, and saves the result to a dedicated
    'outputs' folder, returning the final file path.

    Args:
        base_image_path (str): Path to the template image.
        text_content (Dict[str, str]): Dictionary of text content to insert.
        output_filename (str): The filename for the generated poster (e.g., "event_poster.png").
        mapping_json_path (str): Path to the JSON file containing field mappings.
                                 If it doesn't exist, it will be created.
        font_path (str): Path to the .ttf or .otf font file.
        logo_paths (Optional[List[str]]): List of paths to logo images. Defaults to None.
        font_sizes (Optional[Dict[str, int]]): Dictionary mapping fields to font sizes. Defaults to None.
        logo_scale (float): Scaling factor for logos. Defaults to 1.0.
        venue_icon_path (Optional[str]): Path to the venue icon image. Defaults to None.
        calendar_icon_path (Optional[str]): Path to the calendar icon image. Defaults to None.
        icon_scale (float): Scaling factor for icons. Defaults to 1.0.

    Returns:
        str: The full path to the saved output image.
        
    Raises:
        FileNotFoundError: If the base image or font file cannot be found.
        ValueError: If the template mapping cannot be created.
    """
    # --- 1. Inputs and Setup ---
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    final_output_path = os.path.join(output_dir, output_filename)

    if not os.path.exists(base_image_path):
        raise FileNotFoundError(f"Base template image not found at: {base_image_path}")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found at: {font_path}")

    # --- 2. Processing: Load or Create Field Mappings ---
    if os.path.exists(mapping_json_path):
        with open(mapping_json_path, 'r') as f:
            mapped_fields = json.load(f)
    else:
        mapped_fields = create_template_mapping(base_image_path, list(text_content.keys()))
        if not mapped_fields:
            raise ValueError("Failed to create template mapping from the base image.")
        with open(mapping_json_path, 'w') as f:
            json.dump(mapped_fields, f, indent=4)

    # --- 3. Processing: Inpaint Original Content ---
    image_cv = cv2.imread(base_image_path)
    mask = np.zeros(image_cv.shape[:2], dtype=np.uint8)
    for key in mapped_fields:
        if 'bbox' in mapped_fields.get(key, {}):
            points = np.array(mapped_fields[key]['bbox'], dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
    
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    inpainted_image_cv = cv2.inpaint(image_cv, mask, 3, cv2.INPAINT_TELEA)
    final_image_pil = Image.fromarray(cv2.cvtColor(inpainted_image_cv, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(final_image_pil, "RGBA")

    # --- 4. Processing: Place Logos ---
    if logo_paths and 'organisation_logo' in mapped_fields:
        logos = [Image.open(p).convert("RGBA") for p in logo_paths if os.path.exists(p)]
        if logos:
            logo_box = mapped_fields['organisation_logo']['bbox']
            min_x, max_x = int(min(p[0] for p in logo_box)), int(max(p[0] for p in logo_box))
            min_y, max_y = int(min(p[1] for p in logo_box)), int(max(p[1] for p in logo_box))
            box_w, box_h = max_x - min_x, max_y - min_y
            
            total_width_ratio = sum(img.width / img.height for img in logos)
            final_h = int(min(box_h, box_w / total_width_ratio) * logo_scale)

            resized_logos = []
            total_w = 0
            for img in logos:
                ratio = final_h / float(img.height)
                new_w = int(img.width * ratio)
                resized_img = img.resize((new_w, final_h), Image.Resampling.LANCZOS)
                resized_logos.append(resized_img)
                total_w += new_w
            
            current_x = min_x + (box_w - total_w) // 2
            paste_y = min_y + (box_h - final_h) // 2
            for logo in resized_logos:
                final_image_pil.paste(logo, (current_x, paste_y), logo)
                current_x += logo.width

    # --- 5. Processing: Place Icons ---
    icon_map = {
        'icon1': venue_icon_path,
        'icon2': calendar_icon_path
    }
    for icon_key, icon_path in icon_map.items():
        if icon_path and os.path.exists(icon_path) and icon_key in mapped_fields:
            with Image.open(icon_path).convert("RGBA") as icon_image:
                icon_box = mapped_fields[icon_key]['bbox']
                min_x, max_x = int(min(p[0] for p in icon_box)), int(max(p[0] for p in icon_box))
                min_y, max_y = int(min(p[1] for p in icon_box)), int(max(p[1] for p in icon_box))
                box_w, box_h = max_x - min_x, max_y - min_y

                target_size = (int(box_w * icon_scale), int(box_h * icon_scale))
                resized_icon = icon_image.copy()
                resized_icon.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                paste_x = min_x + (box_w - resized_icon.width) // 2
                paste_y = min_y + (box_h - resized_icon.height) // 2
                final_image_pil.paste(resized_icon, (paste_x, paste_y), resized_icon)

    # --- 6. Processing: Draw Text Content ---
    font_sizes = font_sizes or {}
    custom_colors = custom_colors or {}
    DEFAULT_FONT_SIZE = 30

    # Backend default font sizes: used when the user does not specify sizes.
    default_font_sizes = {
        'type_of_event': 55,
        'campus_name': 45,
        'department_name': 50,
        'about_event': 35,
        'venue': 25,
        'date': 25,
        'time': 25
    }

    # Merge user overrides onto defaults. If user passes an empty dict or None,
    # the defaults are used. If user provides some keys, they override defaults.
    if font_sizes:
        merged = default_font_sizes.copy()
        # only accept numeric overrides for safety
        for k, v in font_sizes.items():
            try:
                merged[k] = int(v)
            except Exception:
                # ignore invalid values and keep default
                pass
        font_sizes = merged
    else:
        font_sizes = default_font_sizes.copy()

    # Debug: log the active font sizes and colors
    try:
        print("DEBUG: active font_sizes=", font_sizes)
        print("DEBUG: custom_colors=", custom_colors)
    except Exception:
        pass
    # Debug: log merged font sizes and incoming colors
    try:
        print("[generate_poster] using font_sizes:", json.dumps(font_sizes))
        print("[generate_poster] incoming custom_colors:", json.dumps(custom_colors))
    except Exception:
        pass
    full_width_center_keys = {'department_name', 'campus_name', 'type_of_event', 'about_event', 'footer'}
    horizontal_padding = 60
    poster_width = final_image_pil.width
    poster_height = final_image_pil.height

    # Fallback vertical positions for keys (fractions of poster height)
    fallback_positions = {
        'campus_name': 0.06,
        'department_name': 0.12,
        'type_of_event': 0.18,
        'about_event': 0.38,
        'speaker 1': 0.55,
        'designation 1': 0.60,
        'date': 0.72,
        'time': 0.76,
        'venue': 0.80,
        'footer': 0.92
    }

    for key, content in text_content.items():
        # If the key isn't in the template mapping, use a sensible fallback box
        if key in mapped_fields and 'bbox' in mapped_fields[key]:
            box = mapped_fields[key]['bbox']
            min_x, max_x = int(min(p[0] for p in box)), int(max(p[0] for p in box))
            min_y, max_y = int(min(p[1] for p in box)), int(max(p[1] for p in box))
            box_w, box_h = max_x - min_x, max_y - min_y
        else:
            # Fallback: full-width area with centered alignment and vertical placement from fallback_positions
            min_x = horizontal_padding
            box_w = poster_width - 2 * horizontal_padding
            frac = fallback_positions.get(key, 0.5)
            # choose a reasonable box height per key
            if key == 'about_event':
                box_h = int(poster_height * 0.18)
            elif key in ('type_of_event', 'department_name', 'campus_name'):
                box_h = int(poster_height * 0.10)
            elif key == 'footer':
                box_h = int(poster_height * 0.08)
            else:
                box_h = int(poster_height * 0.06)
            min_y = int(poster_height * frac) - box_h // 2
            # ensure min_y is within image bounds
            min_y = max(0, min(min_y, poster_height - box_h))

    # Use custom color if provided, else fallback to contrast color
        color_str = custom_colors.get(key, '')
        if color_str:
            # Basic color name to RGB mapping (expand as needed)
            color_map = {
                'black': (0,0,0), 'white': (255,255,255), 'red': (255,0,0), 'green': (0,128,0), 'blue': (0,0,255),
                'yellow': (255,255,0), 'orange': (255,165,0), 'purple': (128,0,128), 'pink': (255,192,203),
                'gray': (128,128,128), 'grey': (128,128,128), 'brown': (165,42,42), 'cyan': (0,255,255), 'magenta': (255,0,255)
            }
            text_color = color_map.get(color_str.lower(), (0,0,0))
        else:
            # if mapped field existed we have max_x/max_y, else compute them from fallback box
            if key in mapped_fields and 'bbox' in mapped_fields[key]:
                bg_min_x, bg_min_y, bg_max_x, bg_max_y = min_x, min_y, max_x, max_y
            else:
                bg_min_x, bg_min_y = min_x, min_y
                bg_max_x = min_x + box_w
                bg_max_y = min_y + box_h
            bg_crop = final_image_pil.crop((bg_min_x, bg_min_y, bg_max_x, bg_max_y))
            avg_color = np.mean(np.array(bg_crop), axis=(0, 1))
            text_color = get_contrasting_color(avg_color)

        current_font_size = font_sizes.get(key, DEFAULT_FONT_SIZE)
        font = ImageFont.truetype(font_path, current_font_size)

        # Debug: log per-key chosen size and color
        try:
            print(f"[generate_poster] key={key} -> font_size={current_font_size}, color={text_color}")
        except Exception:
            pass

        wrap_width = poster_width - (2 * horizontal_padding) if key in full_width_center_keys else box_w

        # Auto-fit logic for 'about_event'
        if key == 'about_event':
            wrapped_text = get_wrapped_text(content, font, wrap_width)
            text_bbox = font.getbbox(wrapped_text)
            text_height = text_bbox[3] - text_bbox[1]
            while text_height > box_h and current_font_size > 10:
                current_font_size -= 2
                font = ImageFont.truetype(font_path, current_font_size)
                wrapped_text = get_wrapped_text(content, font, wrap_width)
                text_bbox = font.getbbox(wrapped_text)
                text_height = text_bbox[3] - text_bbox[1]

        wrapped_text = get_wrapped_text(content, font, wrap_width)
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        draw_x = (poster_width - text_width) / 2 if key in full_width_center_keys else min_x + (box_w - text_width) / 2
        draw_y = min_y + (box_h - text_height) / 2

        # Debug: log what will be drawn for this key
        try:
            print(f"DEBUG: draw key='{key}' size={current_font_size} color={text_color}")
        except Exception:
            pass

        draw.text((draw_x, draw_y), wrapped_text, font=font, fill=text_color, align='center')

    # --- 7. Output: Save the Final Image ---
    final_image_pil.save(final_output_path)
    return final_output_path


# ==============================================================================
# EXAMPLE USAGE (for testing purposes)
# ==============================================================================
if __name__ == "__main__":
    # This block will only run when the script is executed directly.
    # It will not run when the `generate_poster` function is imported elsewhere.
    
    # --- 1. Define Paths and Asset Locations ---
    # NOTE: You must create these asset folders and place your files inside them.
    # assets/
    #   - original_poster.png
    #   - mapping.json (optional, will be created)
    # fonts/
    #   - custom_font.ttf
    # logos/
    #   - logo1.png
    #   - logo2.png
    # icons/
    #   - venue.png
    #   - calendar.png

    # Define all file and asset paths
    base_template_path = "assets/original_poster.png"
    mapping_file_path = "assets/mapping.json"
    font_file_path = "fonts/custom_font.ttf"
    list_of_logo_paths = ["logos/goal4.png", "logos/goal9.png"]
    venue_icon_file_path = "icons/venue.png"
    calendar_icon_file_path = "icons/calendar.png"

    # --- 2. Define the Content for the Poster ---
    poster_text_content = {
        'campus_name': "Bangalore Central Campus",
        'department_name': "Department of Computer Science",
        'type_of_event': "Annual Tech Fest\nCode Genesis 2025",
        'about_event': "A hands-on workshop exploring the latest advancements in Generative AI, from foundational models to practical applications.",
        "speaker 1": "Dr. Evelyn Reed",
        "designation 1": "Chief AI Scientist, Futura Corp",
        'date': "August 22, 2025",
        'time': "9:00 AM - 12:00 PM",
        'venue': "Central Block, 10th Floor, Campus View",
        'footer': "School of Sciences\nDesigned by AI"
    }

    # Define custom font sizes for specific text fields
    custom_font_sizes = {
        'type_of_event': 55,
        'campus_name': 45,
        'department_name': 50,
        'about_event': 35,
        'venue': 25,
        'date': 25,
        'time': 25
    }

    # --- 3. Call the Generator Function ---
    try:
        # The main function call with all parameters
        generated_file_path = generate_poster(
            base_image_path=base_template_path,
            text_content=poster_text_content,
            output_filename="generated_poster.png",
            mapping_json_path=mapping_file_path,
            font_path=font_file_path,
            logo_paths=list_of_logo_paths,
            logo_scale=1.0,
            font_sizes=custom_font_sizes,
            venue_icon_path=venue_icon_file_path,
            calendar_icon_path=calendar_icon_file_path,
            icon_scale=1.0
        )
        print(f"✅ Poster generation complete! Find it at: {generated_file_path}")

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ An error occurred during poster generation: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"❌ An unexpected error occurred: {e}")