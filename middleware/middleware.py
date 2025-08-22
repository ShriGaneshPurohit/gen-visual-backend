# middleware.py
# This file contains the middleware logic to process prompts from the frontend and convert them to JSON format for the backend.
import os
import requests
import json
from dotenv import load_dotenv

def process_prompt(prompt: str) -> dict:
    """
    Process the incoming prompt string and convert it to the expected JSON format for the backend.
    This version uses simple keyword extraction to fill the fields if present in the prompt.
    """
    import re

    # Detect unsupported or ambiguous commands early and return a user-friendly message.
    # Examples: "make me a coffee", "change it" (without a target), etc.
    lower_prompt = (prompt or "").lower()
    unsupported_patterns = [r"\bmake me a coffee\b", r"\bcoffee\b", r"\bbrew coffee\b", r"\border\b", r"\bsend money\b"]
    for pat in unsupported_patterns:
        if re.search(pat, lower_prompt):
            # Return only a short message so the frontend can display it directly.
            return {'message': "Sorry, I can't do that. You can ask me to change colors, fonts, or text."}

    # If the user issues a vague change like "change it" or "do it" without naming a field,
    # return a helpful guidance message instead of attempting LLM parsing.
    vague_phrases = ["change it", "do it", "make it", "do that", "change that"]
    field_keywords = ['title', 'type of event', 'campus', 'department', 'about', 'venue', 'date', 'time', 'footer']
    if any(p in lower_prompt for p in vague_phrases) and not any(k in lower_prompt for k in field_keywords):
        return {'message': "Sorry, I can't do that. You can ask me to change colors, fonts, or text."}

    # Default values (used as fallback)
    default_poster_text_content = {
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

    custom_font_sizes = {
        'type_of_event': 55,
        'campus_name': 45,
        'department_name': 50,
        'about_event': 35,
        'venue': 25,
        'date': 25,
        'time': 25
    }

    # New: Style extraction (color/font size)
    custom_colors = {
        'type_of_event': '',
        'campus_name': '',
        'department_name': '',
        'about_event': '',
        'venue': '',
        'date': '',
        'time': '',
        'footer': ''
    }

    import re
    # Map common field names to keys (defined once)
    field_map = {
        'type_of_event': 'type_of_event',
        'title': 'type_of_event',
        'campus name': 'campus_name',
        'department name': 'department_name',
        'about event': 'about_event',
        'venue': 'venue',
        'date': 'date',
        'time': 'time',
        'footer': 'footer'
    }

    # Font size extraction (e.g., "make the venue font size 30")
    font_size_pattern = re.compile(r"make the ([\w ]+) font size (\d+)", re.IGNORECASE)
    for match in font_size_pattern.finditer(prompt):
        field = match.group(1).strip().replace('title', 'type_of_event').replace('event name', 'type_of_event')
        size = int(match.group(2))
        # Map common field names to keys
        field_map = {
            'type_of_event': 'type_of_event',
            'title': 'type_of_event',
            'campus name': 'campus_name',
            'department name': 'department_name',
            'about event': 'about_event',
            'venue': 'venue',
            'date': 'date',
            'time': 'time',
            'footer': 'footer'
        }
        key = field_map.get(field.lower(), field.lower().replace(' ', '_'))
        if key in custom_font_sizes:
            custom_font_sizes[key] = size

    # Relative size extraction (e.g., "make the title bigger")
    relative_size_pattern = re.compile(r"(?:make|change) the ([\w ]+?) (bigger|smaller)", re.IGNORECASE)
    for match in relative_size_pattern.finditer(prompt):
        field_raw = match.group(1).strip()
        field = field_raw.replace('title', 'type_of_event').replace('event name', 'type_of_event')
        action = match.group(2).lower()
        key = field_map.get(field.lower(), field.lower().replace(' ', '_'))
        # If user said 'title' or similar, map to type_of_event
        if key not in custom_font_sizes and field_raw.lower() in ('title', 'event name'):
            key = 'type_of_event'
        if key in custom_font_sizes:
            try:
                current = int(custom_font_sizes.get(key, 0))
            except Exception:
                current = 0
            if action == 'bigger':
                custom_font_sizes[key] = (current + 10) if current else (default_poster_text_content and 55)
            elif action == 'smaller':
                custom_font_sizes[key] = max(8, current - 8) if current else 30

    # Color extraction (multiple variants)
    color_pattern1 = re.compile(r"(?:make|change) the ([\w ]+?) (?:color|font color|text color)? ?to (\w+)", re.IGNORECASE)
    color_pattern2 = re.compile(r"(?:make|change) the ([\w ]+?) (\w+)", re.IGNORECASE)
    for match in color_pattern1.finditer(prompt):
        field = match.group(1).strip().replace('title', 'type_of_event').replace('event name', 'type_of_event')
        color = match.group(2).strip()
        key = field_map.get(field.lower(), field.lower().replace(' ', '_'))
        if key in custom_colors:
            custom_colors[key] = color

    # catch simple patterns like 'make the title blue'
    for match in color_pattern2.finditer(prompt):
        field = match.group(1).strip()
        color_candidate = match.group(2).strip()
        # only accept color_candidate if it's a color word (not keywords like 'bigger')
        if color_candidate.lower() in ('black','white','red','green','blue','yellow','orange','purple','pink','gray','grey','brown','cyan','magenta'):
            field = field.replace('title', 'type_of_event').replace('event name', 'type_of_event')
            key = field_map.get(field.lower(), field.lower().replace(' ', '_'))
            if key in custom_colors:
                custom_colors[key] = color_candidate

    # Handle pronoun-based color changes like 'change its color to red'
    pronoun_color = re.search(r"change (?:its|their) color to (\w+)", prompt, re.IGNORECASE)
    if pronoun_color:
        color = pronoun_color.group(1).strip()
        # find last mentioned field in the prompt (simple heuristic)
        last_field = None
        for token in re.finditer(r"(title|type of event|campus name|department name|about event|venue|date|time|footer)", prompt, re.IGNORECASE):
            last_field = token.group(0)
        if last_field:
            lf = last_field.replace('title', 'type_of_event').replace('event name', 'type_of_event')
            key = field_map.get(lf.lower(), lf.lower().replace(' ', '_'))
            if key in custom_colors:
                custom_colors[key] = color

        # LLM (Gemini) integration


    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        # Try to load from .env manually if not set
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    print("GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))

    # Gemini API endpoint (v1beta, correct model and header)
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" if GEMINI_API_KEY else None

    # System prompt for the LLM
    system_prompt = (
        "Extract the following fields from the user prompt and return them as a JSON object with these keys: "
        "campus_name, department_name, type_of_event, about_event, speaker 1, designation 1, date, time, venue, footer. "
        "For 'about_event', keep it short (max 15 words) but detailed. "
        "If a field is missing, use an empty string. Respond ONLY with the JSON object."
    )

    llm_response = None
    if GEMINI_API_URL:
        try:
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": system_prompt + "\nPrompt: " + prompt}]}
                ]
            }
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            }
            resp = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=10)
            print("LLM raw response:", resp.text)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    import re
                    # Try to extract JSON from the LLM response
                    text = candidates[0]["content"]["parts"][0]["text"]
                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if match:
                        llm_response = json.loads(match.group(0))
            else:
                print(f"LLM HTTP error: {resp.status_code}")
        except Exception as e:
            print("LLM Exception:", e)


    poster_text_content = default_poster_text_content.copy()
    if llm_response:
        for k in poster_text_content:
            if k in llm_response and llm_response[k]:
                poster_text_content[k] = llm_response[k]

    # Post-process 'designation 1' to remove any '\n' (let rendering logic handle line breaks)
    desig = poster_text_content.get('designation 1', '')
    if desig:
        poster_text_content['designation 1'] = desig.replace('\\n', '').replace('\n', '').strip()

    result = {
        'poster_text_content': poster_text_content,
        'custom_font_sizes': custom_font_sizes
    }
    # Only include custom_colors if any color is set
    if any(v for v in custom_colors.values()):
        result['custom_colors'] = custom_colors
    return result

# Example usage (for testing):
if __name__ == "__main__":
    test_prompt = "Generate a poster for World Trade Organization event."
    result = process_prompt(test_prompt)
    print(result)
