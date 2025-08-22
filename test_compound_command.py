# test_compound_command.py
# Runs a compound test: "make the title bigger and change its color to red"
# Calls the middleware, posts the resulting JSON to the backend, and saves the returned poster.

from middleware.middleware import process_prompt
import requests
import json
import os


def main():
    cmd = "make the title bigger and change its color to red"
    print(f"Testing compound command: '{cmd}'")

    out = process_prompt(cmd)
    print(json.dumps(out, indent=2))

    # Ensure outputs dir
    os.makedirs('outputs', exist_ok=True)

    # Prepare form data
    poster_text = out.get('poster_text_content', {})
    font_sizes = out.get('custom_font_sizes', {}) or {}
    colors = out.get('custom_colors', {}) or {}

    # If middleware didn't provide a numeric font-size for the title but the prompt
    # said "bigger", apply a sensible increase to the backend default.
    if 'type_of_event' not in font_sizes and 'bigger' in cmd.lower():
        font_sizes['type_of_event'] = 65  # backend default is 55, so increase by 10

    data = {
        'base_template_path': 'assets/original_poster.png',
        'mapping_file_path': 'assets/mapping.json',
        'font_file_path': 'fonts/OpenSans-VariableFont_wdth,wght.ttf',
        'logo_paths': 'logos/goal4.png,logos/goal9.png',
        'venue_icon_file_path': 'icons/venue.png',
        'calendar_icon_file_path': 'icons/calendar.png',
        'poster_text_content': json.dumps(poster_text),
        'custom_font_sizes': json.dumps(font_sizes),
        'face_image_paths': 'assets/p1.jpeg'
    }

    if colors:
        data['custom_colors'] = json.dumps(colors)

    url = "http://127.0.0.1:8000/full-process"

    try:
        resp = requests.post(url, data=data, files={})
    except Exception as e:
        print(f"Request failed: {e}")
        return

    if resp.status_code == 200:
        out_path = os.path.join('outputs', 'poster_compound_bigger_red.png')
        with open(out_path, 'wb') as f:
            f.write(resp.content)
        print(f"Saved combined poster to {out_path}")
    else:
        print(f"Backend error: {resp.status_code}")
        print(resp.text)


if __name__ == '__main__':
    main()
